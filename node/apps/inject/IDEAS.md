# topics

## TODO

- --require
- --eval?

- --interactive (can this be used on electron apps?)

## Claude desktop app

```sh
# optional, adds more output:
export DEBUG="*"
# TODO look into other commands to run, would like to find a way to enable nodeIntegration (if I wanna really dig in)

# start w/ remote debugging (open about:inspect in Brave and connect to localhost:8315)
#    open any of the sub-processes! and can inject scripts then like tampermonkey to mod the page (its the same as the web page as far as the front end)
/Applications/Claude.app/Contents/MacOS/Claude --remote-debugging-port=8315


```
## asar

```fish
npm install -g asar
asar list --is-pack /Applications/Claude.app/Contents/Resources/app.asar
# some files aren't inlined in asar... binaries
asar extract /Applications/Claude.app/Contents/Resources/app.asar ~/wherver/unpacked
asar pack --unpack "{*.node,*.dll}" ~/wherever/unpacked /Applications/Claude.app/Contents/Resources/app.asar
# so far, this has not worked for me, the Claude app crahses afterwards, otherwise I find the file to modify to mod nodeIntegration:
#   ./vite/build/index.js:
#       webPreferences:{preload:Ve.join(U.app.getAppPath(),".vite/build/mainWindow.js"),additionalArguments:BE(),contextIsolation:false,nodeIntegration:true}})
#         I added the contextIsolation:false, nodeIntegration:true... FYI this is not the cause of the crash as I was not able to even repack the original and get it to work.
```

## DONE

- --inspect[-brk] (et al)

