# Snapshot Tool for RDS

The Snapshot Tool for RDS automates the task of creating manual snapshots, copying them into a different account and a different region and deleting them after a specified number of days. It also allows you to specify the backup schedule (at what times and how often) and a retention period in days. 

Run the Cloudformation templates on the same region where your RDS instances run (both in the source and destination accounts). If that is not possible because AWS Step Functions is not available, you will need to use the SourceRegionOverride parameter.

## Getting Started

Deploy snapshot-tool-source.yaml in the source account (the account that runs the RDS instances)

Deploy snapshot-tool-dest.yaml in the destination account (the account where you'd like to keep your snapshots)

## Source Account

The following components will be created in the source account:
•	3 Lambda functions (TakeRDSSnapshotsLambda, ShareRDSSnapshotsLambda, DeleteOldRDSSnapshotsLambda)
•	3 State Machines (Amazon Step Functions) to trigger execution of each Lambda function (TakeRDSSnapshotsStateMachine, ShareRDSSnapshotsStateMachine, DeleteOldRDSSnapshotsStateMachine)
•	3 Cloudwatch Event Rules to trigger the state functions
•	3 Cloudwatch Alarms and associated SNS Topics to alert on State Machine failures
•	A Cloudformation stack containing all these resources

## Destination Account

The following components will be created in the destination account:
•	2 Lambda functions (CopyRDSSnapshotsLambda, DeleteOldRDSSnapshotsLambda)
•	2 State Machines (Amazon Step Functions) to trigger execution of each Lambda function (CopyRDSSnapshotsDestStateMachine, DeleteOldRDSSnapshotsDestStateMachine)
•	2 Cloudwatch Event Rules to trigger the state functions
•	2 Cloudwatch Alarms and associated SNS Topics to alert on State Machine failures
•	A Cloudformation stack containing all these resources

## How it Works

There are two sets of Lambda Step Functions that take regular snapshots and copy them across. Snapshots can take time, and they do not signal when they're complete. Snapshots are scheduled to begin at a certain time using CloudWatch Events. Then different Lambda Step Functions run periodically to look for new snapshots. When they find new snapshots, they do the sharing and the copying functions.

## In the Source Account

A CloudWatch Event is scheduled to trigger Lambda Step Function State Machine named TakeRDSSnapshotsStateMachine. That state machine invokes a function named TakeRDSSnapshotsLambda. That function triggers a snapshot and applies some standard tags. It matches RDS instances using a regular expression on their names.

There are two other state machines and lambda functions. The ShareRDSSnapshotsStateMachine looks for new snapshots created by the TakeRDSSnapshotsLambda function. When it finds them, it shares them with the destination account. This state machine is, by default, run every 10 minutes. If it finds a new snapshot that is intended to be shared, it shares the snapshot.

The other state machine is the DeleteOldRDSSnapshotsStateMachine and it calls DeleteOldRDSSnapshotsLambda to delete snapshots according to the RetentionDays parameter when the stack is launched. This state machine is, by default, run once each hour. If it finds a snapshot that is older than the retention time, it deletes the snapshot.

## In the Destination Account

There are two state machines and corresponding lambda functions. The CopyRDSSnapshotsDestStateMachine looks for new snapshots that have been shared but have not yet been copied. When it finds them, it creates a copy in the destination account, encrypted with the KMS key that has been stipulated. This state machine is, by default, run every 10 minutes. 

The other state machine is just like the corresponding state machine and function in the source account. The state machine is DeleteOldRDSSnapshotsDestStateMachine and it calls DeleteOldRDSSnapshotsLambda to delete snapshots according to the RetentionDays parameter when the stack is launched. This state machine is, by default, run once each hour. If it finds a snapshot that is older than the retention time, it deletes the snapshot.




