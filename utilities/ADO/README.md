### scope
This script helps to automatically discover all the ADO orgs and projects accessible by the user and add them to target Semgrep org as SCM connections.
It will also enumerate all the connections to enable auto-scan and incoming webhooks.

### known limitations:
when there is new org/orgs being added to the Azure subscription, Semgrep.dev will not be automatically discover them or add them, and we need to run the script again to do so.

### usage

```
python3 -m venv venv
source venv/bin/activate
./venv/bin/pip install requests
python list-and-add-2-scm.py
Authenticated as: Shi Chao (shi@semgrep.com)

✅ Found 2 organization(s).

=== Organization: sandbox-shichao ===
  → Found 3 project(s).
    Creating Semgrep SCM config for: sandbox-shichao/mini-demo
      ✅ Created sandbox-shichao/mini-demo (Config ID: 47781)
      → Subscribing to webhook for config 47781...
         ✅ Webhook subscription successful for sandbox-shichao/mini-demo.
    Creating Semgrep SCM config for: sandbox-shichao/dummy
      ✅ Created sandbox-shichao/dummy (Config ID: 47782)
      → Subscribing to webhook for config 47782...
         ✅ Webhook subscription successful for sandbox-shichao/dummy.
    Creating Semgrep SCM config for: sandbox-shichao/paytm-demo
      ✅ Created sandbox-shichao/paytm-demo (Config ID: 47783)
      → Subscribing to webhook for config 47783...
         ✅ Webhook subscription successful for sandbox-shichao/paytm-demo.

=== Organization: ooo-devops ===
  → Found 2 project(s).
    Creating Semgrep SCM config for: ooo-devops/semgrep
      ✅ Created ooo-devops/semgrep (Config ID: 47784)
      → Subscribing to webhook for config 47784...
         ✅ Webhook subscription successful for ooo-devops/semgrep.
    Creating Semgrep SCM config for: ooo-devops/sandbox
      ✅ Created ooo-devops/sandbox (Config ID: 47785)
      → Subscribing to webhook for config 47785...
         ✅ Webhook subscription successful for ooo-devops/sandbox.
```

### the script is made idempotent, so you could run it multiple times
```
python list-and-add-2-scm.py
Authenticated as: Shi Chao (shi@semgrep.com)

✅ Found 2 organization(s).

=== Organization: sandbox-shichao ===
  → Found 3 project(s).
    Creating Semgrep SCM config for: sandbox-shichao/mini-demo
      ⚠️  sandbox-shichao/mini-demo already exists in Semgrep. Skipping webhook creation.
    Creating Semgrep SCM config for: sandbox-shichao/dummy
      ⚠️  sandbox-shichao/dummy already exists in Semgrep. Skipping webhook creation.
    Creating Semgrep SCM config for: sandbox-shichao/paytm-demo
      ⚠️  sandbox-shichao/paytm-demo already exists in Semgrep. Skipping webhook creation.

=== Organization: ooo-devops ===
  → Found 2 project(s).
    Creating Semgrep SCM config for: ooo-devops/semgrep
      ⚠️  ooo-devops/semgrep already exists in Semgrep. Skipping webhook creation.
    Creating Semgrep SCM config for: ooo-devops/sandbox
      ⚠️  ooo-devops/sandbox already exists in Semgrep. Skipping webhook creation.
```
