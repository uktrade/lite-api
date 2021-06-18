How to release
==============

Figure out the version of the release
-------------------------------------

1. Go [here](https://github.com/uktrade/lite-api/compare). 
2. Choose the last release tag and master.
3. This will give you a summary of all the changes that have been merged to master since the last release.

Based on this changeset, we can determine the new version of the API using semantic versioning. t;dr -

> Given a version number MAJOR.MINOR.PATCH, increment the:
> MAJOR version when you make incompatible API changes,
> MINOR version when you add functionality in a backwards compatible manner, and
> PATCH version when you make backwards compatible bug fixes.

At the end of this exercise, you should know the new version of the API.

Tag the release
---------------

1. Go [here](https://github.com/uktrade/lite-api/releases/new).
2. Put the new version in `Tag Version`.
3. `Release Title` should be something like `LITE API v<your-version>`.
4. Description should include the list of PRs (optionally JIRA tickets) that are included in the release. It is also a good practice to break this list down into features and bugfixes.
5. Hit `Publish Release`.

Deploy to Demo
--------------

1. Go [here](https://jenkins.ci.uktrade.digital/job/lite-api/).
2. Hit `Build with Parameters`.
3. Choose `Tag version` and `demo` for environment. (We can also choose the `master` but there is a risk of deploying ticket that are still under product review)
4. Hit `Build`.
5. When the build finishes, put the following message in the Teams channel - "Hey <friend-from-product>, LITE API v<your-version> is deployed on demo and ready for product review before release to prod."

Deploy to Prod
--------------

1. When product approves the release, go [here](https://jenkins.ci.uktrade.digital/job/lite-api-PROD/).
2. Hit `Build with Parameters`, choose `Tag version` and hit `Build`.
3. When the build is finished, keep an eye on Sentry for a while to make sure nothing funny is happening. 
4. Under the previous message on Teams channel, type - "LITE API v<your-version> is now on prod".
