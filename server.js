const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

// Import routes avec debug
console.log('Loading routes...');

const authRoutes = require('./routes/auth');
console.log('authRoutes type:', typeof authRoutes, authRoutes);

const courseRoutes = require('./routes/courses');
console.log('courseRoutes type:', typeof courseRoutes, courseRoutes);

const exerciseRoutes = require('./routes/Exercise');
console.log('exerciseRoutes type:', typeof exerciseRoutes, exerciseRoutes);

const uploadRoutes = require('./routes/uploads');
console.log('uploadRoutes type:', typeof uploadRoutes, uploadRoutes);

const errorHandler = require('./middleware/errorHandler');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/mecaflow', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('Connected to MongoDB'))
.catch(err => console.error('MongoDB connection error:', err));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/courses', courseRoutes);
app.use('/api/exercises', exerciseRoutes); // ✅ Corrigé : exerciseRoutes au lieu d'ExerciseRoutes
app.use('/api/uploads', uploadRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use(errorHandler);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});