// models/Product.js
const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const ProductSchema = new Schema({
  name: {
    type: String,
    required: [true, 'Product name is required']
  },
  price: {
    type: Number,
    required: [true, 'Product price is required']
  },
  description: {
    type: String
  }
}, {
  timestamps: true, // Tự động thêm 2 trường createdAt và updatedAt
  versionKey: false  // Không tạo trường __v
});

module.exports = mongoose.model('Product', ProductSchema);