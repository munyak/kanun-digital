# Kanun Digital - Deployment Notes

## To Deploy the New Premium Site

### 1. Set Up Formspree (REQUIRED before going live)

The forms currently point to a placeholder Formspree endpoint. You need to:

1. Go to https://formspree.io/
2. Sign up with contact@kanun.digital (or your preferred email)
3. Create a new form
4. Copy your form endpoint (looks like `https://formspree.io/f/xxxxxxxx`)
5. Update these files with your actual endpoint:
   - `previews/premium-jay/index.html` (two places: contact form & newsletter)

Search for `formspree.io/f/xwpkpqvd` and replace with your actual endpoint.

### 2. Copy Files to Production Root

```bash
cd /Users/geoffrey/.openclaw/workspace/kanun-digital

# Backup current production
cp index.html index-backup.html

# Copy premium version to root
cp previews/premium-jay/index.html ./index.html
cp previews/premium-jay/thank-you.html ./thank-you.html

# Copy brand assets
cp -r brand/ ./brand/
```

### 3. Update Paths for Production

In the new `index.html`, update:
- `../../brand/favicon.svg` → `/brand/favicon.svg` (already done)
- Any other relative paths

### 4. Create OG Image

The site references `/brand/og-image.png` - you need to create this:
- Dimensions: 1200x630px
- Include: Logo + tagline
- I can generate this if needed

### 5. Deploy

```bash
cd /Users/geoffrey/.openclaw/workspace/kanun-digital
git add .
git commit -m "Deploy premium site redesign with professionals section"
git push origin main  # or whatever your deploy branch is
```

### Form Alternative (if Formspree isn't set up yet)

You can temporarily change the form to use mailto:

```html
<form action="mailto:contact@kanun.digital" method="POST" enctype="text/plain">
```

This will open the user's email client - not ideal but works as fallback.

---

## What's New in This Version

1. **Premium Visual Design** - Jay Shetty-inspired editorial aesthetic
2. **Abstract Hero** - Animated gradient orbs instead of stock video
3. **Expanded Professionals Section** - Detailed resources for therapists & attorneys
4. **Functional Forms** - Ready for Formspree integration
5. **New Brand Identity** - Minimal K mark logo
6. **Thank You Page** - Post-submission confirmation
7. **Improved SEO** - Updated meta tags and structured data

---

*Last updated: Feb 8, 2026*
