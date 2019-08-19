## Tags

Tags are used strictly for development purposes, and shouldn't be used in CircleCI or Jenkins.

### Tags in use

#### ```@tag('only')```

Only run tests tagged with 'only':
```--tag=only```

#### ```@tag('slow')```

Exclude slower to run tests:
```--exclude-tag=slow```

> You should only add the slow tag to your test when it has a significant impact on time; always review with another member of the team to make sure you absolutely need it.