import { register } from 'node:module';

register('./custom-loader.js', import.meta.url);
