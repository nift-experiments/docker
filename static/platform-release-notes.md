# Accounts and admin release notes


This page lists new features, enhancements, known issues, and bug fixes for
Docker accounts and admin features, including Docker Home, billing, security,
and subscriptions.

## 2026-09-30

### Bug fixes and enhancements

- Accounts that already have cloud sandboxes skip
  [Docker Agentic Platform](/subscription-billing/plans/docker-agentic-platform/)
  checkout.

## 2026-09-29

### New

- Organization owners can now
  [assign a license to a team](/accounts/organization/manage/manage-licenses/#teams).
  Every member of the team receives the license, including people who join the
  team later. Each member uses one license per product.
- The
  [Licenses page](/accounts/organization/manage/manage-licenses/#view-licenses)
  in Docker Home shows how many licenses are available and whether they are
  assigned to teams or to individual members.

## 2026-09-28

### Bug fixes and enhancements

- [Creating a team](/accounts/organization/manage/manage-a-team/#create-a-team)
  in Docker Home opens that team's page.
- The
  [member list CSV](/accounts/organization/manage/members/#export-a-member-list-csv)
  includes a **Licenses** column when the organization has at least one active
  license pool. The column lists each member's assigned licenses.

## 2026-09-24

### New

- You can now subscribe to the
  [Docker Agentic Platform](/subscription-billing/plans/docker-agentic-platform/)
  pay-as-you-go plan with a personal account to run agents in cloud
  sandboxes. Compute is metered by the second while a sandbox runs.

### Bug fixes and enhancements

- The [support request form](https://app.docker.com/support/contact) **Legal**
  topic includes **PII/Sensitive information**, **Service abuse**, and
  **Trademark takedowns**.

## 2026-09-14

### New

- Organization owners can now
  [export a member list](/accounts/organization/manage/members/#export-a-member-list-csv)
  from Docker Home and receive the CSV by email. Docker generates the file
  asynchronously and emails a download link to the owner.

## 2026-08-20

### New

- [Docker Verified Publisher](/subscription-billing/plans/docker-verified-publisher/)
  Starter and Growth plans are now available via self-serve. Organizations
  can apply and subscribe without contacting sales.

## 2026-08-14

### New

- Administrators can now
  [select a product license when inviting a member](/accounts/organization/manage/manage-licenses/#licenses-and-invites).
  Docker assigns the license when the invitee accepts.

## 2026-07-31

### New

- Administrators can now create
  [OIDC connections](/security/authentication/oidc-connections/)
  so GitHub Actions workflows authenticate to Docker with short-lived tokens
  instead of stored personal or organization access tokens. Available for
  Docker Team, Docker Business, Docker Hardened Images, and Docker Sponsored
  Open Source organizations.

## 2026-06-18

### New

- Custom roles now include
  [AI Governance permissions](/security/roles-and-permissions/custom-roles/permissions-reference/#ai-governance)
  so owners can delegate policy management to other users and teams.

## 2026-06-02

### New

- Administrators can now provision products to organization members with
  [licenses](/accounts/organization/manage/manage-licenses/).
  Licenses were introduced with AI Governance. Owners can assign or revoke
  them from the Members page, or turn on automatic assignment when a member
  first uses a supported product.

## 2026-05-19

### New

- You can now purchase
  [Gordon Plus, Max, and Ultra plans](/subscription-billing/plans/gordon/)
  for personal accounts from the billing portal in Docker Home.
- Organizations can now purchase
  [DHI Select](/subscription-billing/plans/dhi/) repositories via
  self-serve from the billing portal in Docker Home.

## 2026-05-12

### New

- [AI Governance](/subscription-billing/plans/ai-governance/) is
  now available. Administrators can purchase licenses through sales,
  [assign them to members](/accounts/organization/manage/manage-licenses/),
  and enforce
  [organization policies](/ai/sandboxes/governance/) for
  Docker AI products from Docker Home.

## 2026-03-03

### New

- [DHI Select](/subscription-billing/plans/dhi/) is now available
  as a Docker Hardened Images plan for organizations that need SLA-backed
  patching and compliance-ready images.

## 2026-02-18

### New

- Administrators can now
  [configure DVP analytics settings](/docker-hub/repos/manage/trusted-content/insights-analytics/#configure-dvp-analytics-settings)
  for consuming domain and benchmark report allocations in the Admin
  Console.

## 2026-02-13

### New

- Administrators can now control whether organization members can push content
  to their personal namespaces on Docker Hub with
  [namespace access control](/desktop/enterprise/hardened-desktop/namespace-access/).
- Administrators can now prevent creating public repositories within
  organization namespaces using the
  [Disable public repositories](/docker-hub/settings/#disable-creation-of-public-repos)
  setting.

## 2026-01-27

### New

- Administrators can now use an allow list with
  [Image Access Management](/desktop/enterprise/hardened-desktop/image-access-management/)
  to approve specific repositories that bypass image access controls.

## 2025-11-04

### New

- Owners can now create
  [custom roles](/security/roles-and-permissions/custom-roles/)
  and assign them to members and teams.

## 2025-10-28

### New

- Docker Business subscribers can now add
  [Premium Support](/support/#paid-subscription-support),
  with faster response times and 24/7 availability.

## 2025-10-22

### New

- Organizations can now
  [pay by invoice](/subscription-billing/manage/payment-method/#pay-by-invoice).

## 2025-10-14

### Bug fixes and enhancements

- Docker Home now keeps
  [activity logs](/accounts/organization/activity-logs/#access-activity-logs)
  for 30 days. Use the Docker Hub API to retrieve older events.

## 2025-10-07

### Bug fixes and enhancements

- Organization management has moved out of Docker Hub. Manage organizations in
  Docker Home.

## 2025-06-30

### New

- Organization owners can now
  [export Docker Desktop user data](/accounts/organization/insights/#export-docker-desktop-user-data)
  from Insights as a CSV file.

## 2025-06-23

### Bug fixes and enhancements

- [Organization access tokens](/security/access-tokens/organization-access-tokens/)
  now work with Docker Scout.

## 2025-06-18

### New

- Organization owners can now
  [resend invitations in bulk](/accounts/organization/manage/members/#manage-invitations)
  from the Members page.

## 2025-06-10

### Bug fixes and enhancements

- [Activity logs](/accounts/organization/activity-logs/) now record
  single sign-on connection changes, and changes to SCIM and just-in-time
  provisioning.

## 2025-05-12

### New

- You can now connect
  [more than one identity provider](/security/authentication/single-sign-on/connect/#configure-multiple-idps)
  to a single sign-on domain. Users choose a provider when they sign in with
  SSO.

## 2025-04-30

### New

- You can now pay for a subscription with a
  [verified US bank account](/subscription-billing/manage/payment-method/#verify-a-bank-account).

## 2025-04-22

### Bug fixes and enhancements

- [Personal access tokens](/security/access-tokens/personal-access-tokens/)
  now transfer to the organization owners when you
  [convert a user account into an organization](/accounts/organization/setup/convert-account/).

## 2025-04-08

### New

- Organization owners can now onboard an organization with
  [guided setup](/accounts/organization/setup/onboard/#onboard-with-guided-setup)
  in Docker Home.

## 2025-04-01

### New

- [Organization access tokens](/security/access-tokens/organization-access-tokens/)
  are now generally available.
- Single sign-on now supports the
  [`dockerSessionMinutes` attribute](/security/provisioning/#sso-attributes),
  so a session can follow the identity provider timeout.
- Administrators can now
  [track whether users comply with Docker Desktop settings policies](/desktop/enterprise/hardened-desktop/settings-management/compliance-reporting/)
  from Docker Home (Early Access). Compliance status is reported by Docker
  Desktop version 4.40 and later.

## 2025-03-12

### New

- You can now
  [disconnect a linked Google or GitHub account](/accounts/individual/manage-account/#manage-connected-accounts)
  from Account settings.

## 2025-03-11

### New

- [Organization access tokens](/security/access-tokens/organization-access-tokens/#available-scopes)
  now include repository scopes and organization management scopes for members,
  invites, and groups.

## 2025-02-21

### Bug fixes and enhancements

- Organization access tokens now work with Docker Build Cloud and the Docker
  Hub APIs. Company owners can manage them.

## 2025-02-11

### New

- Docker Home and the Docker Admin Console are now generally available.

## 2025-01-31

### Bug fixes and enhancements

- Docker began collecting VAT for all European countries on March 1, 2025. See
  [Sales tax exemption and VAT](/subscription-billing/manage/tax-certificate/).

## 2025-01-30

### New

- Installing Docker Desktop via the PKG installer is now generally available.
- Enforcing sign-in via configuration profiles is now generally available.

## 2025-01-10

### Bug fixes and enhancements

- [Activity logs](/accounts/organization/activity-logs/) now record
  when a settings policy is created, updated, deleted, or transferred.

## 2024-12-10

### New

- New Docker subscriptions are now available. For more information, see
  [Docker subscriptions and features](https://www.docker.com/pricing?ref=Docs&refAction=DocsPlatformReleaseNotes)
  and
  [Announcing Upgraded Docker Plans: Simpler, More Value, Better Development and Productivity](https://www.docker.com/blog/november-2024-updated-plans-announcement/).

## 2024-11-18

### New

- Administrators can now:
  - Enforce sign-in with
    [configuration profiles](/desktop/enterprise/enforce-sign-in/methods/#configuration-profiles-method-mac-only)
    (Early Access).
  - Enforce sign-in for more than one organization at a time (Early Access).
  - Deploy Docker Desktop for Mac in bulk with the
    [PKG installer](/desktop/enterprise/enterprise-deployment/pkg-install-and-configure/)
    (Early Access).
  - [Use Desktop Settings Management via the Docker Admin Console](/desktop/enterprise/hardened-desktop/settings-management/configure-admin-console/)
    (Early Access).

### Bug fixes and enhancements

- Enhanced Container Isolation (ECI) has been improved to:
  - Permit administrators to
    [turn off Docker socket mount restrictions](/desktop/enterprise/hardened-desktop/enhanced-container-isolation/config/#allowing-all-containers-to-mount-the-docker-socket).
  - Support wildcard tags when using the
    [`allowedDerivedImages` setting](/desktop/enterprise/hardened-desktop/enhanced-container-isolation/config/#docker-socket-mount-permissions-for-derived-images).

## 2024-11-11

### New

- [Personal access tokens](/security/access-tokens/personal-access-tokens/)
  (PATs) now support expiration dates.

## 2024-10-15

### New

- Beta: You can now create
  [organization access tokens](/security/access-tokens/organization-access-tokens/)
  (OATs) to enhance security for organizations and streamline access
  management for organizations in the Docker Admin Console.

## 2024-08-29

### New

- Deploying Docker Desktop via the
  [MSI installer](/desktop/enterprise/enterprise-deployment/msi-install-and-configure/)
  is now generally available.
- Two new methods to
  [enforce sign-in](/desktop/enterprise/enforce-sign-in/)
  (Windows registry key and `.plist` file) are now generally available.

## 2024-08-24

### New

- Administrators can now view
  [organization Insights](/accounts/organization/insights/).

## 2024-07-17

### New

- You can now centrally access and manage Docker products in
  [Docker Home](https://app.docker.com).

