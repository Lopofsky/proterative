# Proterative (Prototype & Declerative)

This is a quick and dirty boilerplate to produce a webapp prototype, based on python's Starlette toolkit.

The workflow is focused as much as possible at the template & SQL Queries. 
ORM(s) were purposefully avoided - no disrespect, It's just a matter of taste, with a salt of objective arguments:

**i)** Since it's a prototype, the final language/framework might differ, so it's better to have raw SQL's, which can be tested "live" until the final data load & transformation is correctly achieved.

**ii)** Faster development: Since the queries themselves are accessible directly from the front-end, they can be edited on the fly, without commits & backend refactoring, via adminer or similar software.

**iii)** Performance. Debatable argument, in the context of a prototype's value, but imho & humble experience, when you want to have an as completed as possible prototype for the client, it's best to squeeze performance for the favor of a smoother user experience, considering the above two reasons as well.

By using internal API's, I try to leverage the capabilities of Jinja2 by providing Query, Forms & Path data, along with (front-end) requested (predefined) DB Queries & optionally data straight from python functions (like flask.Blueprint/starlette.Route do with jinja2 & locals) to the template's disposal. 

A significant part of the business logic will take place at the template & the DB Queries, but hey, it's a solution for fast prototyping!


## Why?

What I'm trying to archive here, is mostly a workflow for full stack developers who want to save time & 
effort while the sales team is still on negotiations with a client.

If an almost feature-complete & working prototype can be obtained as soon as possible, it's easier to make modifications 
& explain to the client questionable demands. 

From my experience it's much easier to convince a client/user, that a demand of theirs might jeopardize the integrity of the system/service, when they can have a hands-on experience with an implementation of their idea.

Of course that approach only covers small demands, after the main project is described & discussed.

Additionally the client will have a peace of mind when they see a working prototype, the discussions on the modifications are easier to take place when they start on the front-end and the developer doesn't have to abstract too much between coding & demands.

Finally the prototype can be part of the final contract, in order to have less misunderstandings & conflicts between the client & the dev team. A WYSIWYG (See=Prototype & Get=The final product which will have the same UI & UX as the prototype) clause.

## Is it fully functional? Can I use it?

Not easily (yet):

**i)** Testing (the most tricky part)

**ii)** Documentation.

**iii)** Dockerfile -> compose + some curating.

**iv)** A postgres docker container with a shared volume with the host & the necessary examples.

**v)** A "meta-admin" for the user to be able to handle the queries/endpoints/users/etc + some monitoring

## Final Notes - Todo's

There are quite a lot waterfall commits & the lack of testing & documentations does the whole project a far from complete idea. However I'm already using it, that's why I'm sharing. The workflow that this boilerplate is supporting is very opinionated, but I'm not :) 

Due to other responsibilities I'm not devoting much time on this, but I'm contributing as much as I can, as soon as I can, with the intend to sanitize the (small) codebase in the future.

Any comments/ideas/questions/criticism are more than welcome :)

P.S. It's heavily not PEP8 friendly :)
