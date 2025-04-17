# Passwordless Authentication System Implementation Plan

This document outlines the step-by-step process for implementing a passwordless authentication system using email-based one-click login.

## Overview

The authentication flow will be:
1. User enters email address on login page
2. System generates a unique token and creates a login link
3. Link is sent to user's email (or displayed in console during development)
4. User clicks link and is automatically authenticated
5. System creates a session for the authenticated user

## Implementation Steps

### 1. Database Schema Updates

- [ ] Create `users` table with at least:
  - `id` (primary key)
  - `email` (unique)
  - `created_at` 
  - `updated_at`
  - `last_login_at`
  
- [ ] Create `login_tokens` table with:
  - `id` (primary key)
  - `user_id` (foreign key to users)
  - `token` (unique, secure random string)
  - `created_at`
  - `expires_at`
  - `used` (boolean, default false)

### 2. User Model

- [ ] Add SQLAlchemy model for User
- [ ] Add SQLAlchemy model for LoginToken
- [ ] Add relationships between models
- [ ] Add helper methods for authentication-related operations

### 3. Authentication Routes

- [ ] Create auth Blueprint (`/auth`)
- [ ] Implement login page route (`/auth/login`)
- [ ] Implement email submission route (`/auth/request-login`)
- [ ] Implement token verification route (`/auth/verify/<token>`)
- [ ] Implement logout route (`/auth/logout`)

### 4. Email Service

- [ ] Create email service abstraction layer
- [ ] Implement development version that prints to console
- [ ] Add login email template
- [ ] Prepare production email service integration points

### 5. Session Management

- [ ] Configure Flask session
- [ ] Implement login/logout functionality
- [ ] Create user session on successful token verification
- [ ] Add session expiry

### 6. Frontend Components

- [ ] Create login form template
- [ ] Add login/logout link in header
- [ ] Add email input validation
- [ ] Create success page after email is sent
- [ ] Create error pages for various authentication scenarios

### 7. User Protection Middleware

- [ ] Create login_required decorator or middleware
- [ ] Add user loader utility
- [ ] Implement current_user context processor

### 8. Security Considerations

- [ ] Implement rate limiting for login requests
- [ ] Set short expiration time for tokens (15-30 minutes)
- [ ] Invalidate tokens after use
- [ ] Use cryptographically secure token generation
- [ ] Prevent timing attacks
- [ ] Implement CSRF protection

### 9. Testing

- [ ] Write unit tests for authentication logic
- [ ] Test the complete login flow
- [ ] Test error cases and edge conditions
- [ ] Test email generation

### 10. Deployment Considerations

- [ ] Configure email service for production
- [ ] Set up environment variables for credentials
- [ ] Configure secure session storage
- [ ] Set appropriate security headers

## Development Implementation Order

1. Create database models and migrations
2. Implement basic auth routes without email sending
3. Add login/logout UI elements
4. Implement token generation and verification
5. Add console-based email service for development
6. Implement session management
7. Add login required protection for routes
8. Add security measures
9. Prepare for production email service integration

## Local Development Mode

During local development:
- Login links will be printed to the console instead of being sent via email
- Debug information will be displayed on error pages
- Sessions may have longer expiration times
- Rate limiting may be disabled

## Production Considerations

For production deployment:
- Configure a reliable email delivery service
- Use HTTPS for all auth routes
- Set appropriate session cookie settings (secure, httpOnly, SameSite)
- Implement proper rate limiting
- Add monitoring for failed login attempts 