# 🚀 Deploy to GitHub Pages - Simple Guide

This guide will help you deploy the CloudCost Optimizer frontend to GitHub Pages.

## Prerequisites

- GitHub account
- Git installed
- Repository pushed to GitHub

---

## 📋 Step-by-Step Deployment

### Step 1: Push Your Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Create GitHub repository at github.com and then:
git remote add origin https://github.com/YOUR_USERNAME/cloudcost-optimizer.git
git branch -M main
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on **Settings** tab
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select:
   - Source: **GitHub Actions**
5. Save

### Step 3: Update Configuration

Before pushing, make sure to update these files:

**frontend/vite.config.js** - Already updated with correct base path:
```javascript
base: '/cloudcost-optimizer/',
```

**README.md** - Update your username:
```markdown
[View Live Application](https://YOUR_USERNAME.github.io/cloudcost-optimizer/)
```

### Step 4: Push and Deploy

```bash
# The GitHub Action will automatically run on push to main
git push origin main
```

### Step 5: Wait for Deployment

1. Go to **Actions** tab in your repository
2. Watch the deployment workflow run (takes 2-3 minutes)
3. Once complete, your site will be live!

---

## 🌐 Access Your Deployed App

Your application will be available at:

```
https://YOUR_USERNAME.github.io/cloudcost-optimizer/
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## 🔧 Troubleshooting

### Issue: 404 Page Not Found

**Solution:** Make sure GitHub Pages is enabled and source is set to "GitHub Actions"

### Issue: Blank Page

**Solution:** Check that `base: '/cloudcost-optimizer/'` is set in `vite.config.js`

### Issue: Deployment Failed

**Solution:** 
1. Check Actions tab for error logs
2. Ensure all dependencies are in package.json
3. Try running `npm run build` locally to verify it works

### Issue: Need to Rename Repository

If you renamed your repository, update the base path in `vite.config.js`:

```javascript
base: '/YOUR-NEW-REPO-NAME/',
```

---

## 📝 Making Updates

After deployment, any changes you push to the main branch will automatically redeploy:

```bash
# Make your changes
git add .
git commit -m "Update feature"
git push origin main

# Wait 2-3 minutes for automatic deployment
```

---

## 🎨 Customization

### Update Repository Name

In `frontend/vite.config.js`:
```javascript
base: '/YOUR-REPO-NAME/',
```

### Update Live Demo Link

In `README.md`:
```markdown
**👉 [View Live Application](https://YOUR_USERNAME.github.io/YOUR-REPO-NAME/)**
```

---

## ✅ Verification Checklist

Before pushing to GitHub:

- [ ] Code is committed
- [ ] `.github/workflows/deploy.yml` exists
- [ ] `vite.config.js` has correct base path
- [ ] README.md has correct live demo link
- [ ] All tests pass locally
- [ ] Frontend builds successfully (`npm run build`)

---

## 🚀 That's It!

Your CloudCost Optimizer is now live and accessible to anyone!

Share your link:
```
https://YOUR_USERNAME.github.io/cloudcost-optimizer/
```

---

## 💡 Pro Tips

1. **Custom Domain**: You can add a custom domain in GitHub Pages settings
2. **HTTPS**: GitHub Pages automatically provides HTTPS
3. **Auto-Deploy**: Every push to main branch automatically deploys
4. **Rollback**: Use git to revert to previous commits if needed

---

**Questions?** Check the main README.md for more details or open an issue on GitHub.
