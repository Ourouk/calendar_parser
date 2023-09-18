# Calendar Parser
This repo contains a simple api to parse Calendar
## Context
As a student with a complicated schedule, following the schedule of multiple years can be complicated, this api permit me to keep track of what I follow
## Features
- Merge multiple calendar from URL into a single one
- extract name of event from the ics
- whitelist or blacklist certain of these event from the merged file 
## How does it work
Create a new ics files :
http://api.domain/parse_calendar_whitelist?URL="https://horaire-hepl.provincedeliege.be/myical.php?groupe=INGG3_B38","https://horaire-hepl.provincedeliege.be/myical.php?groupe=INGI4_M18"&whitelist="unix - INGG3-110-01/01 D\u00c3\u00a9veloppement logiciel1-HIARD Samuel"
Where URLs point to different ics files and the whitelist contain that should be available in the final calendar.
To get available events name you can use for example :
http://127.0.0.1:5000/available_events?URL="https://horaire-hepl.provincedeliege.be/myical.php?groupe=INGG3_B38","https://horaire-hepl.provincedeliege.be/myical.php?groupe=INGI4_M18"