# User Guide
1. Start the server and open http://127.0.0.1:8000.
2. Type a goal, e.g. `calculate (45+15)*3 and count words in this sentence`. Separate steps with "and", "then" or commas.
3. Watch the Live Execution Monitor: plan, risk, execution, verification (with confidence and evidence).
4. Protected actions (`fetch_url`, `delete_file`) show **Approve / Deny** buttons. No answer in 2 minutes = denied.
5. Try `simulate unstable failure` to see retries and self-healing fallback.
6. Click **Verify integrity** to check the audit hash chain.

Tools: calculator, summarize, word_count, write_note, fetch_url (example.com, wikipedia.org only), delete_file (sandbox only).
