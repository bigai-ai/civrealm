The following are some common issues that you may encounter when running the code. If you encounter any other issues, please feel free to open an issue.

* Note that each game corresponds to one port on the server. If one game just stops and you immediately start a new game connecting to the same port as the stopped game, the new game may encounter errors and exit. Our training has used ''Ports.get()'' in ''civrealm/freeciv/utils/port_utils.py'' to avoid the situation. If you want to configure the client port and start a client manually, you need to find the available ports by checking the 'Online Games/MULTIPLAYER' tab in localhost:8080.

* If firefox keeps loading the page, please try to add the following line to `/etc/hosts`:

    ```bash
    127.0.0.1 maxcdn.bootstrapcdn.com
    127.0.0.1 cdn.webglstats.com
    ```