module.exports = {
  env: {
    node: true,
    es2021: true
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  overrides: [
    {
      files: ['**/*.js'],
      rules: {
        'no-undef': 'off' // To avoid errors with Playwright globals
      }
    }
  ],
  rules: {
    'no-console': 'off',
    'no-unused-vars': 'warn'
  }
}; 