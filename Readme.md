For more information see [http:/friggeri.net/blog/a-genetic-approach-to-css-compression/](http:/friggeri.net/blog/a-genetic-approach-to-css-compression/).

#Usage

`python css.py test.css` Simplest possible usage, prints result to stdout
`python css.py test.css --output test-gbc.css` Put the result in specified file
`python css.py test.css --gzip 9` use gzip to weight the algorithm rather than raw size
`python css.py test.css other.css` concatenate the two files together before running the algorithm
