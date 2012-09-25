This directory contains several CSS files in `css`, those ending in `-gbc.css`
where compressed using a genetic optimization of biclique covering.

#Caveat

The files in this directory have been minified, in order to evaluate the gain of
genetic bipartite compression compared to simple minification.

Since the parser does not understand several CSS3 constructs (eg. `@keyframes`,
etc.) and that these are actually untouched by the compression, I took the
liberty of stripping those away from the source files, once again in order to
make a fair comparison between simple minification and genetic bipartite
compression.

#CSS Test Files

  * `test.css` Minimal test file
  * `friggeri.css` Stylesheet from my web page
  * `bootstrap.css` Twitter bootstrap (with `@keyframes` removed)
  * `google.css` CSS present on [google.com](http://google.com)
  * `pygments.css` Basic stylesheet obtained by running `pygmentize -S default -f html`
  * `hackernews.css` Stylesheet served on [Hacker * News](http://news.ycombinator.com)
  * `stackoverlow.css` Stylesheet from [StackOverflow](http://stackoverflow.com)
