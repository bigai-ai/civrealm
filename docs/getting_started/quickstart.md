### Testing the installation

To test if the installation is successful, run

```bash
test_civrealm 
```

To test with multiple players, run:

```bash
test_civrealm --minp=2 --username=myagent
```

Then start another terminal and run:

```bash
test_civrealm --username=myagent1
```

To observe the game play, you can access http://localhost:8080/ on a browser. Then, please click the "Online Games" button. You can find the running game under the "MULTIPLAYER" tab.