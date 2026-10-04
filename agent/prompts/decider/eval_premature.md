---
type: noul
fail: "The request is missing something the output needed; ask the user for it instead of guessing."
criteria:
  "true": "The output had to guess or assume something the user did not provide (a topic, a name, a value, a target), so the assistant should ask a clarifying question first."
  "false": "The user's text gives everything the task needs; answering now is appropriate."
---

Is it premature to answer this request before asking the user for something they did not provide?
