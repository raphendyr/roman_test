#!/usr/bin/env node
'use strict';

const fs = require('fs')
const path = require('path')
const DSStore = require('ds-store')

const exit_with_error = (err) => {
  console.error(err);
  process.exit(1)
}

const create_ds_store = () => {
  const ds = new DSStore()

  const w = 760
  const h = 480
  const x = 300
  const y = 200
  const ixpos = 200
  const iypos = 200

  ds.vSrn(1)
  ds.setIconSize(128)
  ds.setBackgroundColor(1, 1, 1)
  ds.setBackgroundPath('/Volumes/Roman/.background/dmg-background.png')
  ds.setWindowSize(w, h)
  ds.setWindowPos(x, y)
  ds.setIconPos('Roman.app', ixpos, iypos)
  ds.setIconPos('Applications', w-ixpos, iypos)

  ds.write('/Volumes/Roman/.DS_Store', (err) => {
    if (err)
      exit_with_error(err)
    else
      console.info("Done")
  })
}

create_ds_store()
