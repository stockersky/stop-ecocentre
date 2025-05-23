# Install javascript dependencies
`npm install`

# Run

## Tailwindcss & flowbyte watch/compile
`npx tailwindcss -i ./assets/static/input.css -o ./assets/static/output.css --watch`

## Lektor

If plugin development ongoing :
`export LEKTOR_DEV=1`

`lektor server`

## build & publish
`lektor build && lektor deploy`

# Notes about authentication on Google API for Blogger articles

## 1) Retrieve or create credentials for Google API
1. go to https://console.cloud.google.com/  
2. go into the associated project
3. click on "APIs and Services"
4. create an OAuth 2.0 Client IDs or update to issue a new credential
5. export credential as json
6. copy the content of this credential into a file named `credential.json` under a directory named `google-blogger-credentials` just a directory up this project (`../google-blogger-credentials` this directory should not be commited onto repo)
7. run locally `lektor build`
8. You'll be redirected to your browser and choose to allow the Google Account owning the Blogger site. 
9. this will generate a `token.json` file in the `../google-blogger-credentials` directory.

> NOTE : this is the only time the 'credential.json' will be used. Next time we run `lektor build` it will use the `token.json` file, 

## 2) Github Actions
1. create a Github Actions Secret named 'GOOGLE_TOKEN' and copy the content (raw) of the `token.json` as value.
2. run the workflow

> Token might expired (1 year ?). In this case, this procedure should be re-executed.
