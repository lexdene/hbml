# hbml

A html template by Python.

## source code

    %html(lang="en")
      %head
        %title hbml page
        %script:plain(type='text/javascript')
          if (foo) {
             bar(1 + 5)
          }
      %body
        %h1 hbml - a html template by Python
        #container.col
          - for i in range(3):
            %div(data-id = i)
              = i + 1
          %p:plain
            hbml is a simple templating
            language writen by Python

## compile to html

    <html lang="en">
      <head>
        <title>hbml page</title>
        <script type="text/javascript">
          if (foo) {
             bar(1 + 5)
          }
        </script>
      </head>
      <body>
        <h1>hbml - a html template by Python</h1>
        <div id="container" class="col">
          <div data-id="0">
            1
          </div>
          <div data-id="1">
            2
          </div>
          <div data-id="2">
            3
          </div>
          <p>
            hbml is a simple templating
            language writen by Python
          </p>
        </div>
      </body>
    </html>
