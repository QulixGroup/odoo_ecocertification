========================
EcoCertification
========================


This module provides a comprehensive environmental certificate management system integrated into Contacts and Website Account pages, helping businesses track supplier compliance and automate certificate lifecycle management.

**Table of contents**

.. contents::
   :local:

Installation
=============

1. Download the module from the Odoo App Store for Odoo 18.0
2. Place the module in your addons folder and extract if necessary
3. From the home screen, go to **Apps** → **Update Apps List**
4. Search for "EcoCertification" and click **Install**

Configuration
=============

1. Login as Administrator and enable Developer mode
2. Add your Admin user to the **Administration / Certificate Administrator** group (user should already be in **Administration / Settings** group)
3. Add supplier users to the **Website / Supplier** group (these should be portal users)
4. Add purchasing staff to the **Certificate Management / Purchase Manager** group
5. Navigate to **Contacts → Configuration → Certificate Categories** and create required categories
6. Navigate to **Contacts → Configuration → Certificate Types** and create required certificate types

Usage
=====

The module provides role-based certificate management with automated notifications and lifecycle tracking.

For All Internal Users:
-----------------------
- View certificates in the dedicated **Environmental Certificates** tab on Contact forms
- Filter contacts by certificate expiration status using smart filters

For Purchase Managers:
-----------------------
- Create and edit certificates from Contact form views
- Access certificate reporting and compliance tracking

For Certificate Administrators:
-------------------------------
- Full control: create, edit, and delete certificates from Contact forms
- Configure certificate types and categories
- Manage system-wide certificate settings

For Suppliers (Portal Users):
-----------------------------
- Access certificates through the Website Account page
- Upload, update, and download their own certificates
- Receive automated email notifications for certificate status changes

Automated Notifications
-----------------------

The system automatically sends email notifications:

- **To Suppliers:** When certificates are expiring (30 days before), expired, or missing
- **To Administrators:** When suppliers upload or update certificates
- **Configurable Frequency:** Modify notification timing in **Settings → Technical → Scheduled Actions** by editing "Environmental Certificates: status notifications"

Certificate Status Tracking
---------------------------

Certificates are automatically classified with visual indicators:

- ✅ **Active** (Green) – More than 30 days before expiration
- ⚠️ **Expiring** (Yellow) – Less than 30 days remaining
- ❌ **Expired** (Red) – Past expiration date

Key Features
============

- **Supplier Portal Integration** – Secure self-service certificate management
- **Flexible Configuration** – Customizable certificate types and categories
- **Smart Filtering** – Quick identification of compliance issues
- **Automated Lifecycle Management** – Daily status checks and notifications
- **Full Audit Trail** – All activities logged in Odoo Chatter
- **Role-Based Access Control** – Appropriate permissions for each user type

Benefits
========

- Avoid costly non-compliance by staying ahead of expiring environmental certificates
- Reduce manual follow-up with automated reminders and clear status indicators
- Empower suppliers to self-manage documentation via secure portal access
- Gain transparency with real-time reporting and comprehensive audit logs

Compatibility
=============
- **Odoo Editions:** Enterprise & Community
- **Version:** 18.0 (fully compatible with latest Odoo frameworks)

Maintainers
===========

This module is maintained by Qulix.

.. image:: https://6477711.fs1.hubspotusercontent-na1.net/hub/6477711/hubfs/Screenshot_13.png?width=108&height=108
   :alt: Qulix Logo
   :target: https://www.qulix.com
   :width: 200px

Qulix is a global provider of end-to-end Odoo solutions that help businesses streamline, automate, and optimize their operations.

For questions or support, please contact: qulix@qulix.com