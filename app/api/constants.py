"""
Static data and constants for the Docket Alert Automation API.
"""

# Hierarchical docket menu structure
DOCKET_CATEGORIES = {
    "Federal Dockets by Court": [
        "U.S. Supreme Court",
        "U.S. Courts of Appeals",
        "Federal District Courts",
        "Federal Bankruptcy Courts",
        "U.S. Tax Court",
        "U.S. Court of Federal Claims",
        "U.S. Court of International Trade",
        "U.S. Judicial Panel on Multidistrict Litigation"
    ],
    "Federal Dockets by Agency": [
        "Copyright Claims Board",
        "Patent Trial & Appeal Board",
        "Securities & Exchange Commission",
        "Trademark Trial & Appeal Board",
        "U.S. International Trade Commission"
    ],
    "Dockets by State": [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
        "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
        "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
        "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
        "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
        "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
        "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ],
    "Dockets by Territory": [
        "Guam",
        "Northern Mariana Islands",
        "Puerto Rico",
        "Virgin Islands"
    ],
    "International": [
        "United Kingdom"
    ],
    "Dockets by Topic": [
        "Admiralty & Maritime",
        "Business & Commercial",
        "Environmental Law",
        "Family Law",
        "Foreign Corrupt Practices Act",
        "Immigration",
        "Insurance",
        "Intellectual Property",
        "Labor & Employment",
        "Real Property",
        "Securities (Federal)",
        "Tax"
    ]
}
