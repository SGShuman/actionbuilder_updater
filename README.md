# Action Builder Membership Synchronization

This project provides a synchronization utility for maintaining consistent **membership status** and **membership type** data between [Action Builder](https://actionbuilder.org) and unit-based organizational data.  

The script detects discrepancies in membership information, generates reports, sends notifications, and cleans up outdated tags to prevent inconsistencies.

It is deployed on Heroku here: https://dashboard.heroku.com/apps/actionbuilder-updater

To add recipient emails, go to Heroku, go to Settings>Reveal Config Vars>Recipient Emails and add to the list by adding a comma like: email@example,email2@example. Currently this is set to run on the 1st of the month. There are roughly 14K entries we have to search; it takes ~8 hours to complete.

---

## Features

- Queries **recently modified people** from Action Builder
- Retrieves each person’s **unit connections** and **current tags**
- Compares **unit-based membership data** with Action Builder tags
- Detects **mismatched membership information**
- Generates **CSV reports**:
  - Excludes inactive members
  - Removes sensitive/internal fields
- Sends the report to configured recipients via email
- Cleans up outdated tags to ensure consistency
- Retries important requests twice

---

## Workflow

1. Query for recently modified people from Action Builder  
2. Retrieve unit connections and membership tags for each person  
3. Compare unit data against Action Builder tags  
4. Identify mismatched membership information  
5. Generate CSV report (excluding inactive members and sensitive fields)  
6. Email the report to configured recipients  
7. Delete outdated tags to maintain clean data  

---

## Project Structure

```
app/
├── api/                     # API clients for Action Builder
│   ├── delete_taggings.py
│   ├── fetch_people.py
│   ├── list_campaigns.py
│   ├── list_people.py
│   ├── list_tags.py
│   ├── search_people.py
│   └── update_person_tagging.py
├── services/                # Internal utilities
│   ├── config.py            # Configuration management
│   └── send_email.py        # Email sending logic (SendGrid)
├── sync/                    # Synchronization logic
│   ├── test/                # (optional) tests
│   └── run_status_type_sync.py  # Main sync script
├── secrets/                 # Local environment secrets
│   └── .env
├── LICENSE
└── README.md
```

---


## Usage

Run the main synchronization script:

```bash
python -m app.sync.run_status_type_sync
```

The script will:
- Check for modified people (default: since yesterday)
- Generate a CSV report of membership mismatches
- Email the CSV report
- Delete outdated tags

---

## CSV Report Format

The generated CSV contains only **active members**, with the following fields:

- `uuid` – Person UUID  
- `unit_name` – Name of the person’s unit  
- `membership_type` – Correct membership type  
---