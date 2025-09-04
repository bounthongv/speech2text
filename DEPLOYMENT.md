# 🚀 Speech Recognition App - Production Deployment Guide

## 📋 Overview

This is a production-ready speech recognition web application with a freemium monetization model:

- **Anonymous Users**: 30 minutes/month
- **Email Users**: 2 hours/month  
- **Supporters**: Unlimited access via Buy Me a Coffee

## 🎯 Quick Deploy Options

### Option 1: Railway (Recommended)

1. **Create Railway Account**: Go to [railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub repository
3. **Deploy**: Railway will auto-detect and deploy
4. **Set Environment Variables**:
   ```
   SECRET_KEY=your-super-secret-key-here
   FLASK_ENV=production
   BMC_USERNAME=your-buymeacoffee-username
   ```

### Option 2: Heroku

1. **Install Heroku CLI**
2. **Deploy**:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   heroku create your-app-name
   heroku config:set SECRET_KEY=your-super-secret-key-here
   heroku config:set FLASK_ENV=production
   heroku config:set BMC_USERNAME=your-buymeacoffee-username
   git push heroku main
   ```

### Option 3: DigitalOcean App Platform

1. **Connect GitHub repo** in DO App Platform
2. **Set environment variables** in the dashboard
3. **Deploy** automatically

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Flask secret key for sessions |
| `FLASK_ENV` | No | development | Set to 'production' |
| `BMC_USERNAME` | No | yourusername | Your Buy Me a Coffee username |
| `FREE_TIER_MINUTES` | No | 30 | Minutes for anonymous users |
| `EMAIL_TIER_MINUTES` | No | 120 | Minutes for email users |
| `PORT` | No | 5000 | Port (auto-set by platforms) |

## 💰 Monetization Setup

### 1. Buy Me a Coffee Integration

1. **Create BMC Account**: [buymeacoffee.com](https://buymeacoffee.com)
2. **Set Username**: Update `BMC_USERNAME` environment variable
3. **Test**: Visit your deployed app and click the coffee button

### 2. User Tiers

- **Anonymous**: 30 min/month, tracked by browser session
- **Email**: 2 hours/month, tracked by email address
- **Supporter**: Unlimited, manual verification for now

## 📊 Analytics & Monitoring

The app automatically tracks:
- User usage by tier
- Session counts
- Monthly resets
- Error logs

Data is stored in JSON files:
- `usage_data.json` - Usage tracking
- `users.json` - User information

## 🔒 Security Features

- Session-based user tracking
- CSRF protection via Flask
- File upload restrictions
- Environment-based configuration
- Production-safe secret key handling

## 🚀 Going Live Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Update `BMC_USERNAME` 
- [ ] Test all user flows
- [ ] Verify usage limits work
- [ ] Test email registration
- [ ] Test BMC integration
- [ ] Monitor error logs
- [ ] Set up domain (optional)

## 📈 Growth Strategy

### Week 1: Launch
- Deploy to production
- Test with friends/family
- Post on social media
- Submit to Product Hunt

### Month 1: User Acquisition
- SEO blog posts
- Reddit/Twitter marketing
- User feedback collection
- Feature improvements

### Month 3: Monetization
- Email marketing to users
- Premium feature development
- API access planning
- Enterprise outreach

## 🛠 Maintenance

### Regular Tasks
- Monitor usage data growth
- Check error logs
- Update dependencies
- Backup user data

### Scaling Considerations
- Move to PostgreSQL for user data
- Add Redis for session management
- Implement proper email verification
- Add payment processing (Stripe)

## 📞 Support

For deployment issues:
1. Check the logs in your platform dashboard
2. Verify environment variables are set
3. Test locally first with `python start.py`
4. Check the GitHub issues for common problems

## 🎉 Success Metrics

Track these KPIs:
- Daily/Monthly Active Users
- Conversion rate (anonymous → email)
- Support rate (email → BMC)
- Average session duration
- Revenue per month

Good luck with your launch! 🚀
