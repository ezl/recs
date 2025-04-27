# Production Database Fix Instructions

## Issue: Missing `google_place_id` Column

If you're encountering the following error in production:

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column activities.google_place_id does not exist
```

Follow these instructions to fix the issue:

## Option 1: Using the Render.com Web Shell

1. Log in to Render.com
2. Navigate to your application dashboard
3. Go to the "Shell" tab
4. Run the following commands:
   ```bash
   # Navigate to the application directory
   cd /opt/render/project/src
   
   # Run the fix script
   python fix_missing_column.py
   
   # If that doesn't work, try running migrations
   export FLASK_APP=run.py
   flask db upgrade
   ```
5. Restart your service from the Render.com dashboard

## Option 2: Triggering a Re-deployment

1. Make a small change to the codebase (e.g., update a comment)
2. Commit and push to the branch that triggers deployment
3. The updated `build.sh` script will run during deployment and apply the fix automatically

## Option 3: Manual SQL Fix

If all else fails, you can connect to the database directly and run the SQL command:

1. Connect to your PostgreSQL database using the connection string from your environment variables
2. Run the following SQL commands:
   ```sql
   ALTER TABLE activities ADD COLUMN google_place_id VARCHAR(255);
   CREATE UNIQUE INDEX ix_activities_google_place_id ON activities (google_place_id);
   ```

## Verification

To verify the fix was applied:

1. After applying one of the fixes above, check the application logs
2. Ensure the error no longer appears
3. Test the functionality that was previously failing

## Preventing Future Issues

To prevent similar issues in the future:

1. Always run migrations as part of your deployment process
2. Test database migrations in a staging environment before deploying to production
3. Keep your local development database in sync with production schemas
4. Use the updated `build.sh` script which includes multiple fallback methods for database setup 