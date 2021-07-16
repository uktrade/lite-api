LTD-1011- System Flags
======================

Context
-------

In LITE there are manually added flags (created by users), and system flags that are automatically applied to cases based on a user action or specified criteria.

It is possible in LITE to create routing rules based off of manually created flags, however if you try and create a rule based around a system flag, the rule doesn’t get applied or run.

Some examples are:

* Range 8 countersigning (which is not the same flag as - ‘Range 8 countersigning destination’)
* Refusal advice (not the same flag as 'refusal')

For the refusal advice flag, this seems to be applied when a user gives refusal advice on a case (after selecting ‘combine all into team advice’). It would be useful to apply a routing rule to this flag, but it is not possible to do that right now, so case officers are having to manually add a ‘refusal’ flag, so that the case can be directed to the correct queue.

What are “system flags” then?
----------------------------

There is no special system flag `type` in LITE.

- Here is the [Flag](https://github.com/uktrade/lite-api/blob/311cf04e0547ed280ae73ebb52fa7c0686eed63c/api/flags/models.py#L16-L36) model.
- Here is the [CSV](https://github.com/uktrade/lite-content/blob/a2336b4ec3a8fee31f773908229b0243fc0af411/lite_api/system_flags.csv#L13) that contains some seed flags that are loaded into the system with the [seedflags](https://github.com/uktrade/lite-api/blob/311cf04e0547ed280ae73ebb52fa7c0686eed63c/api/staticdata/management/commands/seedflags.py) command.

Unfortunately, the flags that are seeded into the system are treated slightly different. E.g.

- They are defined [here](https://github.com/uktrade/lite-api/blob/311cf04e0547ed280ae73ebb52fa7c0686eed63c/api/flags/enums.py#L73-L109).
- The `/flags` endpoint has a special [filter](https://github.com/uktrade/lite-api/blob/311cf04e0547ed280ae73ebb52fa7c0686eed63c/api/flags/views.py#L94-L97) for system flags.
- It doesn't seem that the FE [uses this filter](https://github.com/uktrade/lite-frontend/blob/464dd34ff0278ded56f7a682d33a9a3ad572f0ca/caseworker/flags/services.py#L12-L23).
- And that is fine because the filter is [completely useless](https://github.com/uktrade/lite-api/blob/311cf04e0547ed280ae73ebb52fa7c0686eed63c/api/flags/views.py#L77). So even if you don't specify `include_system_flags`, the endpoint includes them anyway. That said, the presence of the filter here implies that this is a bug and not a feature. System flags were never meant to be returned by default in the `/flags` response.

This last point begs the question - **Why?**

My guess is that this is because of the fact that unlike user flags which are specified by the users and therefore dynamic in nature, system flags can be relied upon to always exist.

In view of this, the code sets and un-sets system flags based on business logic. E.g. The `set_case_flags_on_submitted_standard_or_open_application` function [here](https://github.com/uktrade/lite-api/blob/311cf04e0547ed280ae73ebb52fa7c0686eed63c/api/applications/libraries/edit_applications.py#L150-L212).

There are bits and pieces of business logic spread across the codebase that checks for certain system flags on cases and acts accordingly. Search `SystemFlags` in this repo and you will see plenty of examples for this.

Why does it matter?
-------------------

Specifically, why does it matter in terms of the context of this ticket i.e. why can't the users create routing rules based off system flags?

Presumably, any routing rules that are created off of system flags would behave in a weird and seemingly unpredictable way as the system flags are set and un-set by the business logic that is baked-in to the code.

In that, I would reckon that (1) we stay away from using system flags in routing rules in general and (2) fix the `/flags` endpoint so that it doesn't include system flags in its response by default. This would mean that instead of -

> when I create routing rules based on system flags, they do not run

We are going to deal with -

> I cannot create routing rules based on system flags

The former is a bug. The latter is a sensible limitation. I would take the latter.
