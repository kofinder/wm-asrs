# Connect UaExpert to the ASRS simulator

1. Start `./gradlew :asrs-simulator:run` from the extracted project root.
2. Launch UaExpert.
3. In the Servers panel choose **Add Server** (plus icon).
4. Choose **Custom Discovery**, and enter `opc.tcp://localhost:12686/milo`.
5. Select the discovered local endpoint with **SecurityPolicy None / MessageSecurityMode None** (only for local development).
6. Connect with **Anonymous** user authentication.
7. Expand **Objects → ASRS → Crane01** in the Address Space pane.
8. Drag `MachineState`, `Position`, `AcceptedCommandId`, and `CompletedCommandId` into Data Access View.
9. Start the WCS in another terminal: `./gradlew :asrs-wcs:bootRun`.
10. Submit a task using `./scripts/test-api.sh`. Watch the values update: ID accepted, machine RUNNING, position changed, ID completed.

**Important:** UaExpert can write the two writable simulator nodes (`TargetLocation`, `CommandId`). Do not modify these at the same time as the WCS. Use them only for a controlled standalone learning exercise; the command write sequence is not atomic.
