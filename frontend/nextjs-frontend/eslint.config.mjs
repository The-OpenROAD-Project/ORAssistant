// eslint.config.js
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import js from '@eslint/js';
import { FlatCompat } from '@eslint/eslintrc';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

const config = [
  {
    ignores: ['.next/**'],
  },
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    rules: {
      // React hooks
      'react-hooks/exhaustive-deps': 'warn',

      // Import/export
      'import/no-anonymous-default-export': 'off',
      'import/order': [
        'error',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            'parent',
            'sibling',
            'index',
          ],
          'newlines-between': 'never',
        },
      ],

      // Code style and readability
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'prefer-const': 'error',

      // React specific
      'react/prop-types': 'off',
      'react/jsx-key': 'error',
      'react/no-array-index-key': 'warn',
      'react/jsx-no-useless-fragment': 'warn',
      'react/jsx-curly-brace-presence': [
        'error',
        { props: 'never', children: 'never' },
      ],

      // Formatting (handled by prettier but good to enforce)
      'max-len': ['warn', { code: 100, ignoreUrls: true }],
      'object-curly-spacing': ['error', 'always'],
      'array-bracket-spacing': ['error', 'never'],
      'comma-dangle': ['error', 'always-multiline'],
      'quote-props': ['error', 'as-needed'],
      quotes: ['error', 'single', { avoidEscape: true }],
      semi: ['error', 'always'],
    },
  },
  ...compat.extends('next/core-web-vitals', 'plugin:prettier/recommended'),
];

export default config;
