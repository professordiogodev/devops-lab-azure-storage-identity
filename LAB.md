# LAB | Azure: Receipts Without Keys

## The situation

Beanie keeps a receipt for every order as a small JSON file in Azure Blob Storage. The first version, written in a hurry, used the **storage account key**: one long string that grants *everything* on the account. It was pasted into an environment variable, then into a screenshot, then into a chat. Last week it appeared in a public repository. Anyone who found it could read every receipt and delete them all.

The fix is not "rotate the key". The fix is to make the key **worthless** and to give the application an identity that can do exactly what it needs, nothing more. In Azure that means three things working together: a storage account that **refuses key-based access**, **managed identities** (identities with no password, handed to a workload by Azure itself), and **role assignments scoped to a single container**. You will build all three, then prove it by running two real containers, one that may write receipts and one that may only read them.

> **Your mission**
> - Create a storage account that is private, TLS-only and **has shared-key access switched off**
> - Discover that being the subscription Owner does not let you read the blobs
> - Create two managed identities and give each exactly one **data-plane** role, scoped to the container
> - Run both identities in real containers and read what Azure allowed and denied
> - Tear it all down and prove it

**Time:** 90-105 min | **Cost:** a few cents | **You need:** an Azure subscription where you can create resources and assign roles, the Azure CLI (`az login` done), curl, Python 3 and a terminal.

---

## Part 0 - Prepare

Fork this repository, clone your fork and run `./setup.sh`. It checks your tools and login and lists the names to use. Everything goes in **`eastus`**, in the resource group **`rg-beanie-receipts`** tagged `lab=azure-storage-identity`. Read `job.sh`: it is what the two containers will run. It uses **no key, no password and no token that you provide**.

---

## Part 1 - A storage account that says no

Create the resource group, then the storage account. The name must be globally unique, 3 to 24 lowercase letters and digits (start it with `st`). Requirements:

- `Standard_LRS`, general purpose v2
- **public blob access disabled**
- **minimum TLS 1.2** and HTTPS only
- **shared-key access disabled** (`--allow-shared-key-access false`)
- tagged `lab=azure-storage-identity`

Then create a **private container** named `receipts`. Use the management plane for the container so that it does not need a key (`az storage container-rm create`).

```bash
az storage account show -g rg-beanie-receipts -n <yours> --query "{shared:allowSharedKeyAccess, public:allowBlobPublicAccess, tls:minimumTlsVersion}"
```

> **Think** With shared-key access off, the account keys still exist and `az storage account keys list` still prints them. What can nobody do with them any more? Why is that better than "rotating the key every 90 days"?

---

## Part 2 - Owner is not enough

You are the Owner of the subscription. Try to list the container:

```bash
az storage blob list --account-name <yours> -c receipts --auth-mode login
```

It fails with `AuthorizationPermissionMismatch`. Read the error. Azure has two planes: the **control plane** (create, configure and delete resources: Owner and Contributor roles) and the **data plane** (read and write what is *inside* them: `Storage Blob Data ...` roles). Owner has the first and not the second, on purpose: the person who manages the account should not automatically read its contents.

> **Predict** If you give yourself `Storage Blob Data Reader` on the *account*, will `az storage blob upload` work? Try it with `--auth-mode login`, then remove the assignment. Keep the error for question 2.

---

## Part 3 - Two identities, two roles, one container

Create two **user-assigned managed identities** in the resource group, tagged: `id-writer` and `id-reader`. Then grant, at the scope of the container `receipts` (the long resource ID ending in `/blobServices/default/containers/receipts`), these and nothing else:

| Identity | Role |
|----------|------|
| `id-writer` | `Storage Blob Data Contributor` |
| `id-reader` | `Storage Blob Data Reader` |

(Use `--assignee-object-id` and `--assignee-principal-type ServicePrincipal`; a brand-new identity needs a few seconds before Entra ID knows it, and role assignments take one or two minutes to take effect.)

```bash
az role assignment list --assignee <principal id> --all -o table
```

> **Think** Why the container and not the account, the resource group or the subscription? Imagine a second container `invoices` is added next month. Which of your assignments would give the receipts writer access to it by accident?

---

## Part 4 - Run both for real

You do not need a virtual machine to use a managed identity. A container instance can carry one. Run the provided script with each identity (read how the identity is passed in: `--assign-identity` on `az container create`, and `az login --identity` inside the script):

```bash
az container create -g rg-beanie-receipts -n job-writer --image mcr.microsoft.com/azure-cli:latest \
  --assign-identity <id-writer resource id> --restart-policy Never --cpu 1 --memory 1.5 --os-type Linux \
  --environment-variables CLIENT_ID=<its client id> ACCOUNT=<your account> RUN=w1 S=$(base64 < job.sh | tr -d '\n') \
  --command-line "/bin/bash -c 'echo \$S | base64 -d | bash'"
az container logs -g rg-beanie-receipts -n job-writer
```

Do the same with `id-reader`. The logs say `READ_OK` or `READ_DENIED` and `WRITE_OK` or `WRITE_DENIED`. The reader should read and be refused when it writes. Look at the exact error code Azure returns.

> **Think** The container never had a password. Follow the token: the script asks a local identity endpoint, Azure returns an Entra ID token for *that identity*, the script presents it to Blob Storage, and the storage service checks the identity's role assignments. Who, in that chain, could a thief impersonate if they stole the container image? If they got a shell inside the running container?

---

## Part 5 - Prove it

```bash
./verify.sh
```

It reads your storage account, container, identities and role assignments, tries the account key (it must be refused), and then runs the two jobs itself and checks what each identity was allowed to do. It takes about 4 minutes. Fix what is red and run it again until it ends with **ALL CHECKS PASSED**. **Paste the output into `SUBMISSION.md` before you tear down.**

> **Stuck?** `AuthorizationPermissionMismatch` for the writer: the role assignment has not propagated yet (wait two minutes) or has the wrong scope. `LOGIN_FAILED` in the job: the identity is not attached to the container, or the client ID is wrong. `StorageAccountAlreadyTaken`: pick another name. `RoleAssignmentExists`: you already created it. The job stays `Waiting`: the image pull takes a minute.

---

## Level up (optional)

- Create a **user delegation SAS** for one blob, valid for 10 minutes (`az storage blob generate-sas --as-user --auth-mode login`). Why does it work when shared-key access is off, and a normal SAS does not?
- Add a **lifecycle management** rule that moves receipts to the cool tier after 30 days and deletes them after 7 years.
- Put the account behind a **private endpoint** and set `--public-network-access Disabled`. How does your laptop read a blob now?
- Turn on **soft delete** and **versioning** for blobs. What do you recover, and what does it cost?

<!-- teardown:start (generated by labs.py, do not edit) -->
## Tear down (mandatory)

Resources left behind cost money, keep doors open and pollute the next lab. Removing what you created is part of the job, so it is part of the submission: **you must prove it is gone**.

Do this **last**, after you have pasted your `verify` output into `SUBMISSION.md` (once you tear down, the lab can no longer be verified).

1. Run `./teardown.sh`. It deletes the resource group `rg-beanie-receipts` (storage account, identities, container jobs and role assignments with them).

Then run the proof:

```bash
./verify-teardown.sh
```

It prints a list of checks and must end with **TEARDOWN VERIFIED**. If it reports leftovers, remove them and run it again. Paste the full output in your submission.
<!-- teardown:end -->

<!-- submission:start (generated by labs.py, do not edit) -->
## Submission

Answer the questions in `SUBMISSION.md` in **your fork** (paste output in code blocks where asked), push, then submit the **URL of your fork**.

**Files to commit**

- `notes.md` with your `az` commands (optional)

**Questions to answer**

1. Paste the commands that created the storage account. Which three settings make it safe by default (public access, TLS, shared key), and what does switching off shared-key access change for anyone who has the account key?
2. As the subscription Owner you tried `az storage blob list --auth-mode login` on your own container and it failed. Paste the error. Why does Owner not mean "can read the data", and which two kinds of roles exist in Azure (control plane vs data plane)?
3. Paste your two role assignments with their scopes. Why did you grant them on the container and not on the storage account or the resource group? What would a writer with Contributor on the subscription be able to do that it must not?
4. Paste the log of the writer job and of the reader job. Which operation did the reader attempt that was denied, and what HTTP status and error code did Azure return?
5. A managed identity has no password. How does the container prove who it is (follow the token: the identity endpoint, the Entra ID token, the storage service)? What happens to the identity when you delete the container?
6. Compare with a SAS token: when would you still hand out a SAS (a user delegation SAS), and why is a SAS signed with the account key a bad idea once key access is off?
7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.
8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.
<!-- submission:end -->
