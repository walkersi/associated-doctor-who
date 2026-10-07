# associated-doctor-who
Maps Doctor Who episodes using tardisguide API for semantle-style games.


## How to use
Place API Key file in code/api/api-key.json
- In format {"id": "public id", "secret": "api key"}
- Control config in code/api/api-config.json
- *Ensure this file is still gitignored!*

Run preprocessor using provided bash script or run story_preprocessor.py then counter.py
- This creates JSONs that are serialised Story objects
- It reads the local CSV for episode slugs, queries TARDIS Guide, and writes to files
- And counts the frequency and value of tropes/characters etc.

Use story_loader.py functions to then acquire Story objects from file system
- Do semantic comparison with their attributes
Use read_counts.py functions to acquire frequency information about story attributes from filesystem preprocessing