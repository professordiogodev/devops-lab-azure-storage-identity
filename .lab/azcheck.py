#!/usr/bin/env python3
import base64, json, os, subprocess, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
RG, LAB = "rg-beanie-receipts", "azure-storage-identity"
passed = failed = 0


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""))


def az(*a, timeout=300, raw=False):
    try:
        r = subprocess.run(("az",) + a + (() if raw else ("-o", "json")), capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            return None
        return r.stdout if raw else (json.loads(r.stdout) if r.stdout.strip() else {})
    except Exception:
        return None


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


print("Subscription %s" % (az("account", "show") or {}).get("name"))
print("== The storage account ==")
rg = az("group", "show", "-n", RG)
check("resource group %s exists, tagged lab=%s" % (RG, LAB), bool(rg) and (rg.get("tags") or {}).get("lab") == LAB, "az group create -n %s -l eastus --tags lab=%s" % (RG, LAB))
if not rg:
    finish()
accts = az("storage", "account", "list", "-g", RG) or []
check("one storage account", len(accts) == 1)
if len(accts) != 1:
    finish()
sa = accts[0]
name = sa["name"]
check("shared-key access is OFF (no account key can sign requests)", sa.get("allowSharedKeyAccess") is False)
check("public blob access is OFF", sa.get("allowBlobPublicAccess") is False)
check("TLS 1.2 minimum and HTTPS only", sa.get("minimumTlsVersion") == "TLS1_2" and sa.get("enableHttpsTrafficOnly") is True)
check("the account is tagged lab=%s" % LAB, (sa.get("tags") or {}).get("lab") == LAB)
cont = az("storage", "container-rm", "show", "--storage-account", name, "-n", "receipts", "-g", RG)
check("container receipts exists and is private", bool(cont) and cont.get("publicAccess") in (None, "None"))
key = az("storage", "account", "keys", "list", "-g", RG, "-n", name, "--query", "[0].value", "-o", "tsv", raw=True)
if key:
    r = subprocess.run(["az", "storage", "blob", "list", "--account-name", name, "-c", "receipts", "--account-key", key.strip(), "-o", "none"], capture_output=True, text=True)
    check("the account key does NOT work (KeyBasedAuthenticationNotPermitted)", r.returncode != 0 and "KeyBasedAuthenticationNotPermitted" in r.stderr, r.stderr[-120:])
else:
    check("the account key does NOT work (could not even list the keys)", True)

print("== The identities and their roles ==")
ids = {i["name"]: i for i in (az("identity", "list", "-g", RG) or [])}
check("two user-assigned managed identities: id-writer and id-reader", {"id-writer", "id-reader"} <= set(ids), "az identity create")
if not {"id-writer", "id-reader"} <= set(ids):
    finish()
cscope = sa["id"] + "/blobServices/default/containers/receipts"
for who, role in (("id-writer", "Storage Blob Data Contributor"), ("id-reader", "Storage Blob Data Reader")):
    ra = az("role", "assignment", "list", "--assignee", ids[who]["principalId"], "--all") or []
    check("%s has exactly one role: %s, scoped to the container (not the account, group or subscription)" % (who, role), len(ra) == 1 and ra[0]["roleDefinitionName"] == role and ra[0]["scope"].lower() == cscope.lower(), str([(r["roleDefinitionName"], r["scope"].split("/")[-1]) for r in ra]))

print("== Run both identities for real (two container jobs, about 3 minutes) ==")
script = open("job.sh").read()
b64 = base64.b64encode(script.encode()).decode()
tag = str(int(time.time()))
groups = {}
for who in ("id-writer", "id-reader"):
    gname = "job-%s-%s" % (who.split("-")[1], tag)
    out = az("container", "create", "-g", RG, "-n", gname, "--image", "mcr.microsoft.com/azure-cli:latest", "--assign-identity", ids[who]["id"],
             "--restart-policy", "Never", "--cpu", "1", "--memory", "1.5", "--os-type", "Linux",
             "--environment-variables", "CLIENT_ID=" + ids[who]["clientId"], "ACCOUNT=" + name, "RUN=" + gname, "S=" + b64,
             "--command-line", "/bin/bash -c 'echo $S | base64 -d | bash'", "--no-wait")
    groups[who] = gname


def logs(g):
    end = time.time() + 420
    while time.time() < end:
        st = az("container", "show", "-g", RG, "-n", g, "--query", "instanceView.state", "-o", "tsv", raw=True)
        if st and st.strip() in ("Succeeded", "Failed"):
            return az("container", "logs", "-g", RG, "-n", g, raw=True) or ""
        time.sleep(10)
    return ""


lw, lr = logs(groups["id-writer"]), logs(groups["id-reader"])
check("the writer identity can write a receipt (WRITE_OK)", "WRITE_OK" in lw, lw[-200:])
check("the reader identity can read the container (READ_OK)", "READ_OK" in lr, lr[-200:])
check("the reader identity is DENIED when it tries to write (WRITE_DENIED)", "WRITE_DENIED" in lr and "WRITE_OK" not in lr, lr[-200:])
for g in groups.values():
    az("container", "delete", "-g", RG, "-n", g, "--yes")
for g in groups.values():
    subprocess.run(["az", "storage", "blob", "delete", "--account-name", name, "-c", "receipts", "-n", "receipt-%s.json" % g, "--auth-mode", "login"], capture_output=True)
finish()
