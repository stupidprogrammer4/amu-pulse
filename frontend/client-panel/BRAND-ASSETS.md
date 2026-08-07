# Using the AMU Pulse icon pack

The client panel is not scaffolded yet, so its complete icon pack is ready in
`public/brand/` for whichever frontend shell is added next.

Add these lines to the future HTML `<head>`:

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="alternate icon" href="/favicon.ico" sizes="any" />
<link rel="apple-touch-icon" href="/brand/apple-touch-icon.png" />
<link rel="manifest" href="/manifest.webmanifest" />
<meta name="theme-color" content="#102a43" />
```

Use `/brand/logo-mark.svg` in the UI and reserve `/brand/logo-mark-mono.svg`
for single-colour contexts.
