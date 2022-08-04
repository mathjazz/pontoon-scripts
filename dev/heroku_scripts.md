### Restore prod DB on stage
Note that `dumpName` is the name of the DB dump created by [Heroku Postgres](https://data.heroku.com/datastores/f5195d27-0c49-415c-81b3-d8e0f9d3bcce#durability).

`heroku pg:backups restore mozilla-pontoon::dumpName DATABASE_URL --app mozilla-pontoon-staging`
