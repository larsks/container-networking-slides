#!/bin/sh

cat > /usr/share/nginx/html/index.html <<EOF
<!DOCTYPE html>
<html>
  <head>
    <title>Container networking demo</title>
  </head>

  <body>
    <h1>Container network demo</h1>

    <p>This is <strong>$(hostname)</strong>.</p>

    <img src="redhat-logo-small.png">
  </body>
</html>
EOF
