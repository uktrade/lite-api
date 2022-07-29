# A Writeup of Case Routing

Case routing is currently driven through two core functions:
- `api/workflow/routing_rules/automation.py:run_routing_rules(case, keep_status)`
- `api/workflow/routing_rules/flagging_rules_automation.py:apply_flagging_rules_to_case(case)`

## run_routing_rules(case, keep_status)
https://github.com/uktrade/lite-api/blob/9dacbc4db18db20f4a051c95e725c8080581383a/api/workflow/automation.py#L12

### Purpose
This function is responsible for taking a case and automatically progressing it based on the case's current state and routing rules present in the system.

A case is progressed by a combination of:
- Assigning it to one or more Queues (Queues are owned by Teams and act as a backlog of cases for each team)
- Changing a Case's status

The function will go through all teams/routing rules and determine whether the state of the case (including it's flags) mean that it satisfies a routing rule and can be assigned to that rule's queue/user.

### Steps
Takes a Case as input and:
- Removes all Queue and GovUser assignments for the case.
- Goes through every team in the system..
    - Get each active routing rule for this team which is applicable for the case's current status
        - Go through each active routing rule in order of `tier` such that Rules with `tier=1` have a chance to apply first and `tier=10` later...
            - Attempt to match the routing rule in question with the current state of the case.  A match is determined by whether the parameter_set of a case is a subset of the parameter_set of a RoutingRule
            - When a match is found, apply the rule by setting the case's attributes as follows:
                - Case is added to the rule's `queue`
                - A `CaseAssignment` is created such that the `user` for the rule is assigned to this case on the queue
            - Multiple rules are applied for a given team so long as they match AND share the same `tier` value
    - Every team has a chance to take a case in to one of their queues via this mechanism; all routing rules are checked for all teams following the above process...
- If no rules were applied, and the function was called with keep_status=False, the case is moved to the next status and all rule checking starts again for this status ^^
- This continues until at least one rule has been applied OR a "terminal" status has been reached

### Called By

#### Exporter Submission of Draft Application

(preceeded by `apply_flagging_rules_to_case(case)`)
https://github.com/uktrade/lite-api/blob/9dacbc4db18db20f4a051c95e725c8080581383a/api/applications/views/applications.py#L413

#### Application Manage Status API endpoint

https://github.com/uktrade/lite-api/blob/master/api/applications/views/applications.py#L531

#### Case Detail PATCH API Endpoint
When this endpoint changes the status of a Case, the routing rules are run.

https://github.com/uktrade/lite-api/blob/master/api/cases/views/views.py#L131
(calls through to change_status() method; https://github.com/uktrade/lite-api/blob/master/api/cases/models.py#L190 )

#### Rerun Routing Rules API Endpoint

https://github.com/uktrade/lite-api/blob/9dacbc4db18db20f4a051c95e725c8080581383a/api/cases/views/case_actions.py#L135

#### user_queue_assignment

During `api/workflow/user_queue_assignment.py:user_queue_assignment_workflow()`
https://github.com/uktrade/lite-api/blob/master/api/workflow/user_queue_assignment.py#L91

Which is in turn called by the following endpoints;
- When a caseworker's assigned queues are changed in AssignedQueues; https://github.com/uktrade/lite-api/blob/71811857bb96e8be66e293b1551e095a0fc57db6/api/cases/views/case_actions.py#L56 and https://github.com/uktrade/lite-api/blob/71811857bb96e8be66e293b1551e095a0fc57db6/api/cases/views/case_actions.py#L78
- When an XML string of cases is imported https://github.com/uktrade/lite-api/blob/a75a8fc90bb1d5d292cda68eed6e265d98b3046e/api/cases/enforcement_check/import_xml.py#L37 (called by the enforcement check endpoint; https://github.com/uktrade/lite-api/blob/3176d25aa6130cd6420f3c2219aafca820bfa39f/api/cases/enforcement_check/views.py#L52)

## apply_flagging_rules_to_case(case)
https://github.com/uktrade/lite-api/blob/3176d25aa6130cd6420f3c2219aafca820bfa39f/api/workflow/flagging_rules_automation.py#L25

### Purpose
This function is responsible for taking a case, reviewing certain criteria (it's type, it's destinations, it's Good's control list entries) and applying flagging rules to it.

As an outcome; the Case, it's Partys, it's Goods should have applicable Flags set according to the flagging rules in the system.

### Steps

- If a case is status Draft or a terminal status, do nothing
- If not, apply the following categories of flagging rules:
    - case-level flagging rules
    - destination-level flagging rules
    - good-level flagging rules

#### Case-level flagging rules
- Case flagging rules are applied so that flagging rules of type case will apply if this Case's CaseType intersects with the case types present in the flagging rule's `matching_values`
- If flagging rule is applied, it's associated flag is set on the case

#### Destination-level flagging rules
- All flagging rule records which are for destinations are collected
- The end user Party records are extracted for the case
- Each party has the applicable flagging rules applied; a rule will apply if the Party's country appears in the flagging rule's `matching_values`
- If flagging rule is applied, it's associated flag is added to the Party

#### Good-level flagging rules
- All flagging rule records for Goods are collected
- The goods are extracted for the Case (this logic is a little complex depending on case types etc)
- Each Good has the applicable flagging rules applied; a rule will apply if:
    - the Good's CLE appears in the flagging rule's `matching_values`, OR...
    - the Good's CLE's parent CLE appears in the flagging rule's `matching_groups`, AND..
    - the Good's CLE/parent CLE is NOT present in the rule's `excluded_values`
- In addition, a flagging rule will not apply if it is `is_for_verified_goods_only=True` AND the Good is not verified
- If flagging rule is applied, it's associated flag is added to the Good

### Called By

#### The EndUserAdvisories POST API Endpoint

https://github.com/uktrade/lite-api/blob/bd4237fd1b8a66c740b7e8e9bf3474e95f0f8198/api/queries/end_user_advisories/views.py#L63

#### The GoodQueriesCreate POST Endpoint

https://github.com/uktrade/lite-api/blob/3176d25aa6130cd6420f3c2219aafca820bfa39f/api/queries/goods_query/views.py#L103

#### The GoodQueryCLCResponse PUT Endpoint

https://github.com/uktrade/lite-api/blob/3176d25aa6130cd6420f3c2219aafca820bfa39f/api/queries/goods_query/views.py#L165

#### The OrganisationDetail PUT Endpoint

When the organisation name has changed, flagging rules are re-applied for all applications in the org:
https://github.com/uktrade/lite-api/blob/b1b70622ac0cef138afdaafc3865f6f228d83da3/api/organisations/views/organisations.py#L177

#### The Case Detail PATCH API Endpoint
When this endpoint changes the status of a Case, the flagging rules are re-applied IF the case status goes from terminal to non-terminal:

https://github.com/uktrade/lite-api/blob/master/api/cases/views/views.py#L131
(calls through to change_status() method; https://github.com/uktrade/lite-api/blob/06db5d78cdf87f2e5e24bca6390670b6e9c3cf11/api/cases/models.py#L177 )

#### Exporter Submission of Application

https://github.com/uktrade/lite-api/blob/3299b2bed4cc55aadd1ff7a9114f434b1ed91cec/api/applications/views/applications.py#L405

#### Application Manage Status API Endpoint

https://github.com/uktrade/lite-api/blob/3299b2bed4cc55aadd1ff7a9114f434b1ed91cec/api/applications/views/applications.py#L515
