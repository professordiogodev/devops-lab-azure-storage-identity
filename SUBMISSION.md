# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `notes.md` with your `az` commands (optional)

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste the commands that created the storage account. Which three settings make it safe by default (public access, TLS, shared key), and what does switching off shared-key access change for anyone who has the account key?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. As the subscription Owner you tried `az storage blob list --auth-mode login` on your own container and it failed. Paste the error. Why does Owner not mean "can read the data", and which two kinds of roles exist in Azure (control plane vs data plane)?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste your two role assignments with their scopes. Why did you grant them on the container and not on the storage account or the resource group? What would a writer with Contributor on the subscription be able to do that it must not?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Paste the log of the writer job and of the reader job. Which operation did the reader attempt that was denied, and what HTTP status and error code did Azure return?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. A managed identity has no password. How does the container prove who it is (follow the token: the identity endpoint, the Entra ID token, the storage service)? What happens to the identity when you delete the container?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Compare with a SAS token: when would you still hand out a SAS (a user delegation SAS), and why is a SAS signed with the account key a bad idea once key access is off?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
