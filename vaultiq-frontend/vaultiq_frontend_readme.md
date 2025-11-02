# VaultIQ Frontend

Modern, responsive React 18 frontend for VaultIQ - an AI-Powered Unified Knowledge Hub for IT Management.

## 🚀 Tech Stack

- **Framework**: React 18
- **Language**: TypeScript (Strict Mode)
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Markdown**: React Markdown (for answer rendering)

## 📁 Project Structure

```
vaultiq-frontend/
├── src/
│   ├── components/
│   │   ├── SearchBar.tsx          # Search input and submit
│   │   ├── AnswerDisplay.tsx      # AI-generated answer with streaming
│   │   └── SourcesDisplay.tsx     # Source cards display
│   ├── hooks/
│   │   └── useApiStream.ts        # Custom hook for API streaming
│   ├── types/
│   │   └── api.ts                 # TypeScript interfaces
│   ├── App.tsx                    # Main application component
│   ├── main.tsx                   # Application entry point
│   └── index.css                  # Tailwind directives
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
└── vite.config.ts
```

## 🛠️ Installation

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see backend README)

### Step 1: Install Dependencies

```bash
cd vaultiq-frontend
npm install
```

### Step 2: Configure Environment

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API Gateway URL:

```env
VITE_API_URL=https://your-api-gateway-url.amazonaws.com/prod
```

For local development with backend running locally:

```env
VITE_API_URL=http://localhost:8000
```

### Step 3: Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## 🏗️ Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 🎨 Features

### 1. Intelligent Search Interface
- Clean, modern search bar with VaultIQ branding
- Quick suggestion chips for common queries
- Loading states with animated spinners
- Disabled state during active searches

### 2. Streaming AI Responses
- Real-time streaming of AI-generated answers
- Progressive text rendering as tokens arrive
- Markdown support for formatted responses
- Animated cursor during streaming

### 3. Source Attribution
- Beautiful card-based source display
- Color-coded by source type (Confluence, Slack, Jira, GitHub)
- Relevance score percentage
- Clickable links to original sources
- Snippet preview with text truncation

### 4. Responsive Design
- Mobile-first approach
- Adaptive layouts for all screen sizes
- Touch-friendly interface
- Optimized for tablets and desktops

### 5. Error Handling
- User-friendly error messages
- Retry functionality
- Network error detection
- Graceful fallbacks

## 🔌 API Integration

### Endpoint

The frontend connects to a single endpoint:

**POST** `/api/query`

### Request Format

```typescript
{
  "query": "How do I deploy to production?",
  "top_k": 5,
  "source_filter": ["confluence", "github"]  // Optional
}
```

### Response Format

```typescript
{
  "answer": "To deploy to production...",
  "sources": [
    {
      "title": "Deployment Guide",
      "url": "https://...",
      "source_type": "confluence",
      "relevance_score": 0.92,
      "snippet": "Production deployment process..."
    }
  ],
  "query": "How do I deploy to production?",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🎯 Component Details

### SearchBar Component

**Props:**
- `isLoading: boolean` - Disables input during API calls
- `onSubmit: (query: string) => void` - Callback when search is submitted

**Features:**
- Controlled input with local state
- Form validation (prevents empty queries)
- Quick suggestion chips
- Animated loading state

### AnswerDisplay Component

**Props:**
- `answer: string` - The AI-generated answer text
- `isStreaming: boolean` - Shows streaming indicator

**Features:**
- Markdown rendering with custom styles
- Syntax highlighting for code blocks
- Responsive typography
- Animated streaming cursor
- Progressive text reveal

### SourcesDisplay Component

**Props:**
- `sources: ApiSource[]` - Array of source documents

**Features:**
- Responsive grid layout (1-3 columns)
- Hover effects for interactivity
- External link handling
- Source type icons and colors
- Relevance score display
- Text truncation with "line-clamp"

### useApiStream Hook

**Returns:**
```typescript
{
  answer: string;
  sources: ApiSource[];
  isLoading: boolean;
  error: string | null;
  query: (request: ApiQueryRequest) => Promise<void>;
  reset: () => void;
}
```

**Features:**
- Streaming response handling
- JSON response parsing
- Error handling
- Loading state management
- Result reset functionality

## 🎨 Tailwind Customization

### Custom Colors

```javascript
primary: {
  50: '#f0f9ff',
  500: '#0ea5e9',
  600: '#0284c7',
  700: '#0369a1',
}
```

### Custom Components

Defined in `index.css`:
- `.card` - Card container with shadow
- `.input-field` - Styled input fields
- `.btn-primary` - Primary action button

## 🧪 Testing

### Manual Testing Checklist

- [ ] Search with valid query
- [ ] Search with empty query (should be disabled)
- [ ] View streaming response
- [ ] Click on source links
- [ ] Test on mobile device
- [ ] Test with long queries
- [ ] Test error states
- [ ] Test loading states

### Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📊 Performance

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: 90+

### Optimization Tips

1. **Code Splitting**: Vite automatically code-splits
2. **Image Optimization**: Use WebP format for images
3. **Bundle Size**: Keep dependencies minimal
4. **Lazy Loading**: Components load on-demand

## 🔒 Security

### Best Practices Implemented

- XSS protection via React's escaping
- External links open in new tab with `noopener noreferrer`
- HTTPS enforcement in production
- CORS handled by backend
- No sensitive data in frontend code

## 🚢 Deployment

### Deploy to AWS S3 + CloudFront

```bash
# Build the app
npm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

## 🐛 Troubleshooting

### API Connection Issues

**Problem**: "API request failed" error

**Solution**:
1. Check `.env` file has correct `VITE_API_URL`
2. Verify backend is running
3. Check CORS configuration on backend
4. Inspect network tab for details

### Streaming Not Working

**Problem**: Answer appears all at once instead of streaming

**Solution**:
1. Check backend sends proper streaming headers
2. Verify `Content-Type` is not `application/json` for streams
3. Ensure backend doesn't buffer responses

### Build Errors

**Problem**: TypeScript errors during build

**Solution**:
```bash
# Clean and reinstall
rm -rf node_modules package-lock.json
npm install

# Check TypeScript version
npm list typescript
```

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vite Guide](https://vitejs.dev/guide/)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📝 License

[Your License Here]

---

**Built with ❤️ using React 18, TypeScript, and Tailwind CSS**