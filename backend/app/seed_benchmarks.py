import os
import json

BENCHMARK_CASES = [
    # Small Features
    {
        "category": "small_features",
        "id": "small_1_dark_mode",
        "problem": "Users complain about eye strain when using the dashboard at night.",
        "solution": "Implement a client-side dark mode toggle in the header.",
        "goals": "Allow users to toggle dark mode instantly. Persist preference across sessions. Align UI colors with accessible contrast guidelines.",
        "template": "## 1. Feature Description\n## 2. UI/UX Behaviors\n## 3. Storage & State Management"
    },
    {
        "category": "small_features",
        "id": "small_2_like_button",
        "problem": "Users lack a quick way to express appreciation for posts, leading to low social engagement.",
        "solution": "Add an interactive 'Like' button on every post card with micro-animations.",
        "goals": "Ensure the button updates UI instantly (optimistic update). Track likes count accurately. Prevent double-liking.",
        "template": "## 1. User Interaction Flow\n## 2. API Schema & Request/Response\n## 3. Edge Cases (Double click, offline)"
    },
    {
        "category": "small_features",
        "id": "small_3_profile_upload",
        "problem": "Profiles look generic and empty because users cannot easily upload custom profile pictures.",
        "solution": "Create a drag-and-drop avatar image uploader with client-side cropping.",
        "goals": "Support JPG/PNG up to 2MB. Preview crop area instantly. Save optimized 150x150 file to CDN.",
        "template": "## 1. Functional Requirements\n## 2. File Validation Rules\n## 3. Error Handling"
    },
    {
        "category": "small_features",
        "id": "small_4_copy_clipboard",
        "problem": "Users manually highlight and copy referral links, frequently making errors or missing characters.",
        "solution": "Add a one-click 'Copy Link' button next to the referral text box.",
        "goals": "Copy full link to clipboard. Show a 'Copied!' tooltip indicator for 2 seconds. Ensure high accessibility.",
        "template": "## 1. Interface Mockup & Elements\n## 2. Browser API Details\n## 3. Fallback Mechanism"
    },
    {
        "category": "small_features",
        "id": "small_5_font_adjuster",
        "problem": "Visually impaired or elderly users struggle to read dense report text tables.",
        "solution": "Provide a simple text-size adjustment widget (+ / A- / Reset) at the top of report views.",
        "goals": "Scale typography dynamically between 12px and 24px. Save preference in local storage. Avoid breaking layout columns.",
        "template": "## 1. Visual Layout\n## 2. Accessibility Guidelines (WCAG)\n## 3. State Management"
    },
    {
        "category": "small_features",
        "id": "small_6_password_toggle",
        "problem": "Users mistype their passwords during sign-up because the input field is masked, leading to frustration.",
        "solution": "Embed an 'eye' icon toggle inside the password input field to reveal or mask characters.",
        "goals": "Allow masking toggle on click. Keep input type secure by default. Prevent autocomplete leaks.",
        "template": "## 1. Component Specs\n## 2. Keyboard Navigation Requirements\n## 3. Security Implications"
    },

    # Medium Features
    {
        "category": "medium_features",
        "id": "medium_1_shopping_cart",
        "problem": "Customers cannot save items for purchase, forcing them to buy items one-by-one.",
        "solution": "Develop a persistent shopping cart service with quantity adjustments and summary calculations.",
        "goals": "Maintain cart items in local state and sync to DB for logged-in users. Calculate taxes and discounts. Limit item quantity based on stock.",
        "template": "## 1. Functional Requirements\n## 2. Database Model Draft\n## 3. API Routes & Cart Logic\n## 4. Checkout CTA Triggers"
    },
    {
        "category": "medium_features",
        "id": "medium_2_user_profile",
        "problem": "Users cannot update their biographical information, security settings, or preferences directly.",
        "solution": "Create a unified Profile Settings page containing General Info, Security, and Notification tabs.",
        "goals": "Allow updates to name, email, and password. Implement email validation. Provide tab-based navigation with unsaved changes warnings.",
        "template": "## 1. Screen Layout & Tabs\n## 2. Form Validation Logic\n## 3. Backend Integration\n## 4. Security Checkpoints"
    },
    {
        "category": "medium_features",
        "id": "medium_3_email_subscription",
        "problem": "Users receive too many generic emails and unsubscribe completely due to lack of preferences control.",
        "solution": "Implement a Subscription Preference Center with granular toggles for newsletters, updates, and promotions.",
        "goals": "Provide checkbox controls. Allow single-click unsubscribe from all emails. Update marketing database in real-time.",
        "template": "## 1. Feature Specifications\n## 2. Data Flow & Integration (ESP)\n## 3. Consent Logging Compliance"
    },
    {
        "category": "medium_features",
        "id": "medium_4_search_autocomplete",
        "problem": "Users struggle to find relevant products because of spelling mistakes and slow search page loading.",
        "solution": "Build an autocomplete search bar that displays matching products and category suggestions as the user types.",
        "goals": "Trigger suggestions after 3 characters. Debounce keyboard inputs by 200ms. Support keyboard selection (arrow keys, Enter).",
        "template": "## 1. UI States (Empty, Typing, Loading, Error)\n## 2. Debounce & Caching Logic\n## 3. API Performance SLAs"
    },
    {
        "category": "medium_features",
        "id": "medium_5_feedback_form",
        "problem": "Standard rating forms get low completion rates due to tedious questions and lack of progress tracking.",
        "solution": "Create a multi-step rating form (Scale 1-10, Category Select, Written Feedback) with progress indicators.",
        "goals": "Design a 3-step wizard. Save partial answers to prevent data loss. Show visual success state at the end.",
        "template": "## 1. Wizard Structure\n## 2. Navigation Rules\n## 3. Analytics Tracking Events"
    },
    {
        "category": "medium_features",
        "id": "medium_6_file_attachment",
        "problem": "Support agents receive tickets without visual context, causing long resolution times.",
        "solution": "Build a file attachment component inside the support ticket creator supporting multiple image/log file uploads.",
        "goals": "Limit upload to 5 files, 5MB each. Display loading progress bars. Support removal of attached files before submission.",
        "template": "## 1. Attachment Specs\n## 2. API Payload Structure\n## 3. Storage Architecture (S3)"
    },

    # Large Flows
    {
        "category": "large_flows",
        "id": "large_1_checkout_pipeline",
        "problem": "High checkout abandonment rate due to complex pages, lack of guest checkout, and vague payment flows.",
        "solution": "Design a structured, linear 3-step checkout flow: Shipping Info, Billing & Payment, and Order Review.",
        "goals": "Support Guest Checkout. Verify shipping addresses using third-party APIs. Process credit cards via Stripe securely.",
        "template": "## 1. Flow Diagram Description\n## 2. Detailed Checkout Steps\n## 3. Error Recovery & Card Validation\n## 4. API Endpoints and Payloads\n## 5. Security & PCI Compliance"
    },
    {
        "category": "large_flows",
        "id": "large_2_user_onboarding",
        "problem": "New signups drop off immediately because the product is complex and lacks guided setup.",
        "solution": "Implement an interactive, multi-step onboarding wizard that guides users through account setup, team invites, and first project creation.",
        "goals": "Create interactive step guides. Allow skipping steps. Track completion progress. Send welcome emails automatically.",
        "template": "## 1. Onboarding Funnel Steps\n## 2. UI Walkthrough Overlays\n## 3. Database Schema for User Progress\n## 4. Dropoff Analytics Triggers"
    },
    {
        "category": "large_flows",
        "id": "large_3_team_invite",
        "problem": "Individual users cannot collaborate with coworkers, limiting viral product growth inside organizations.",
        "solution": "Design a complete workspace member management and invitation flow with role-based access control.",
        "goals": "Allow bulk email invites. Manage workspace roles (Owner, Admin, Editor, Viewer). Secure invite validation token logic.",
        "template": "## 1. RBAC Matrix & Role Descriptions\n## 2. Invite Token Generation & Expiry\n## 3. UI Workspaces Panel\n## 4. Backend Validation APIs"
    },
    {
        "category": "large_flows",
        "id": "large_4_billing_portal",
        "problem": "SaaS customers must email support manually to upgrade plans, cancel subscriptions, or download PDF invoices.",
        "solution": "Integrate a comprehensive Stripe Customer Billing Portal for subscription tier modifications and card updates.",
        "goals": "Show current tier and billing cycle. Allow seamless upgrade/downgrade with prorated charges. Display download links for historical invoices.",
        "template": "## 1. Tier Pricing Matrix\n## 2. Stripe Webhook Handler Architecture\n## 3. Plan Change Logic & Entitlement Sync"
    },
    {
        "category": "large_flows",
        "id": "large_5_oauth_sign_in",
        "problem": "Friction during login leads to low signup rates. Users forget passwords and drop out.",
        "solution": "Implement secure passwordless OAuth 2.0 authentication utilizing Google, GitHub, and email magic links.",
        "goals": "Ensure single-click login. Auto-merge accounts with matching email addresses. Issue JWT tokens securely with CSRF checks.",
        "template": "## 1. Authentication Handshakes\n## 2. Account Merge Rules\n## 3. JWT Schema & Cookie Policy\n## 4. Security Audit Considerations"
    },
    {
        "category": "large_flows",
        "id": "large_6_notification_system",
        "problem": "Users miss important system events because they are not actively watching the application.",
        "solution": "Build a real-time notification engine feeding in-app notifications, push notifications, and emails.",
        "goals": "Support real-time WebSockets connection. Group notifications by day. Provide mark-all-as-read buttons. Manage notification frequency preferences.",
        "template": "## 1. Notification Feed Layout\n## 2. WebSocket Connection Flow\n## 3. DB Queue Design & PubSub\n## 4. Delivery Channel Routing Logic"
    },

    # Edge Cases
    {
        "category": "edge_cases",
        "id": "edge_1_offline_sync",
        "problem": "Mobile app users lose typed inspection logs if they drive through areas with spotty internet connectivity.",
        "solution": "Build an offline synchronization database queue using IndexedDB that auto-merges local drafts back to the cloud.",
        "goals": "Queue modifications offline. Retry sync on reconnect. Detect and resolve conflict version collisions gracefully.",
        "template": "## 1. Local Database Schema\n## 2. Network Check & Retry Logic\n## 3. Conflict Resolution Protocol\n## 4. Fail-safe Storage Limits"
    },
    {
        "category": "edge_cases",
        "id": "edge_2_concurrent_editing",
        "problem": "Multiple team members edit the same project settings simultaneously, causing newer updates to overwrite older ones.",
        "solution": "Implement optimistic locking with last-writer-wins warning indicators and document locking notifications.",
        "goals": "Acquire lock when editing starts. Notify other viewers of the lock. Warn user if a save collision occurs.",
        "template": "## 1. Lock Lifecycle & States\n## 2. API Request Lock/Release\n## 3. UI Warning Modals\n## 4. Database Transaction Control"
    },
    {
        "category": "edge_cases",
        "id": "edge_3_payment_retry",
        "problem": "Network hiccups during payment processing result in duplicate charges or silent, unlogged subscription cancellations.",
        "solution": "Design an idempotent billing pipeline that retries failed transactions and runs webhook handlers safely.",
        "goals": "Enforce Stripe idempotency keys. Queue failed payments for exponential backoff retries. Lock account access if retries fail after 3 days.",
        "template": "## 1. Idempotency Key Architecture\n## 2. Retry Schedule & Billing Rules\n## 3. Webhook Failures Recovery Plan"
    },
    {
        "category": "edge_cases",
        "id": "edge_4_rate_limiting",
        "problem": "Automated web scrapers overload API servers, degrading response times for actual paying customers.",
        "solution": "Implement a distributed API rate limiting middleware using Redis token bucket mechanism.",
        "goals": "Limit public endpoints to 60 requests/min and authenticated to 1000/min. Return HTTP 429 with Retry-After header. Support API key tier exceptions.",
        "template": "## 1. Rate Limiting Rules & Tiers\n## 2. Redis Token Bucket Algorithm\n## 3. Header Specifications\n## 4. Bypass Protocols"
    },
    {
        "category": "edge_cases",
        "id": "edge_5_gdpr_deletion",
        "problem": "Manual database scripting to delete user profiles takes hours and leads to compliance tracking issues.",
        "solution": "Develop an automated Privacy Deletion Workflow ensuring full GDPR right-to-be-forgotten execution across main and secondary systems.",
        "goals": "Delete personal data from main DB. Hard-delete or anonymize analytical data. Propagate deletion to email newsletters and backups.",
        "template": "## 1. Deletion Execution Flow\n## 2. Anonymization Rules\n## 3. Verification Log & Status Updates"
    },
    {
        "category": "edge_cases",
        "id": "edge_6_mfa_recovery",
        "problem": "Users lose access to their authenticator apps, locking them out of accounts permanently.",
        "solution": "Implement an MFA recovery process featuring backup codes and administrative identity verification overrides.",
        "goals": "Generate 8-digit secure recovery codes on sign-up. Allow lock bypass using a recovery code once. Log recovery attempts.",
        "template": "## 1. Recovery Code Specs\n## 2. Lockout Override Workflows\n## 3. Audit Logging Security"
    },

    # Template Based
    {
        "category": "template_based",
        "id": "template_1_api_spec",
        "problem": "Integrating developers make mistakes because API parameters, schemas, and endpoints are not formal.",
        "solution": "Create a unified, developer-facing API Specification document structure for all microservices.",
        "goals": "Publish API standards. Enforce OpenAPI JSON specification structure. Group endpoints logically.",
        "template": "## 1. API Metadata\n## 2. Authentication Protocol\n## 3. Endpoints & Methods\n## 4. JSON Error Payloads\n## 5. Client SDK Guidelines"
    },
    {
        "category": "template_based",
        "id": "template_2_security_audit",
        "problem": "Security reviews are inconsistent, missing vital validation steps like CSRF, CORS, and secret leaks.",
        "solution": "Implement a pre-deployment Security Compliance checklist template that all code releases must pass.",
        "goals": "Establish vulnerability rating rules. Document sanitization policies. Standardize cryptography guidelines.",
        "template": "## 1. Security Overview\n## 2. OWASP Top 10 Checklist\n## 3. Key Management & Secrets\n## 4. External Penetration Auditing"
    },
    {
        "category": "template_based",
        "id": "template_3_db_migration",
        "problem": "Database migrations occasionally cause query lockouts and downtime because there are no written runbooks.",
        "solution": "Design a strict Database Migration Plan template requiring forward/backward compatibility checks.",
        "goals": "Document rollback queries. Enforce lock-safe indexing syntax. Validate staging test migrations.",
        "template": "## 1. Schema Change Details\n## 2. Migration Execution Commands\n## 3. Zero-Downtime Strategy (Expand/Contract)\n## 4. Rollback Scripts"
    },
    {
        "category": "template_based",
        "id": "template_4_sla_tracking",
        "problem": "Customers drop off because performance issues go unmonitored until an outage occurs.",
        "solution": "Establish an SLA tracking template defining availability metrics, latency bounds, and incident response times.",
        "goals": "Define SLA boundaries (99.9% uptime). Outline response times based on severity levels. Schedule monthly reviews.",
        "template": "## 1. Service Catalog & Scope\n## 2. SLO Thresholds (P95, P99 Latency)\n## 3. Incident Severity Definitions\n## 4. Refund / Credit Policies"
    },
    {
        "category": "template_based",
        "id": "template_5_partner_integration",
        "problem": "Integrating with external fulfillment vendors takes weeks because integration steps are unstructured.",
        "solution": "Write a standardized Integration Partner Onboarding guide detailing connection handshakes, webhook contracts, and sandbox testing.",
        "goals": "Define webhook validation signatures. Describe sandbox configurations. Standardize API logs.",
        "template": "## 1. Connection Requirements\n## 2. Authentication & Signatures\n## 3. Sandbox Testing Procedures\n## 4. Launch Checklist"
    },
    {
        "category": "template_based",
        "id": "template_6_rbac_access",
        "problem": "Auditors flag access controls because system permissions are added ad-hoc without formal request records.",
        "solution": "Establish an Internal Tool Access Control policy matrix template defining role assignments and permission scopes.",
        "goals": "Map administrative permissions. Define temporary access expiration times. Mandate dual-authorization for superuser actions.",
        "template": "## 1. Roles Definition Matrix\n## 2. Permission Levels (Read, Write, Admin)\n## 3. Approval Workflows\n## 4. Revocation & Expiry Rules"
    }
]

def seed_filesystem():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_dir = os.path.join(base_dir, "..", "benchmark")
    
    print(f"Seeding benchmark cases to filesystem path: {os.path.abspath(benchmark_dir)}...")
    
    for case in BENCHMARK_CASES:
        category_dir = os.path.join(benchmark_dir, case["category"])
        os.makedirs(category_dir, exist_ok=True)
        
        file_path = os.path.join(category_dir, f"{case['id']}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "id": case["id"],
                "problem": case["problem"],
                "solution": case["solution"],
                "goals": case["goals"],
                "template": case["template"]
            }, f, indent=2)
            
    print(f"Successfully seeded {len(BENCHMARK_CASES)} cases in filesystem.")

if __name__ == "__main__":
    seed_filesystem()
