'use strict';

// Import model Product đã tạo
const Product = require('../models/Product');

/**
 * Create a new product
 **/
exports.createProduct = function(body) {
  return new Promise(async function(resolve, reject) {
    try {
      const newProduct = new Product(body);
      const savedProduct = await newProduct.save();
      // OpenAPI spec yêu cầu trả về 201, nên ta trả về payload và mã status
      resolve({ code: 201, payload: savedProduct });
    } catch (error) {
      // Trả về lỗi nếu có
      reject({ code: 400, payload: { message: error.message } });
    }
  });
}

/**
 * Delete a product
 **/
exports.deleteProduct = function(productId) {
  return new Promise(async function(resolve, reject) {
    try {
      const deletedProduct = await Product.findByIdAndDelete(productId);
      if (!deletedProduct) {
        // Nếu không tìm thấy sản phẩm, trả về lỗi 404
        return reject({ code: 404, payload: { message: 'Product not found' } });
      }
      // OpenAPI spec yêu cầu 204 No Content, không cần payload
      resolve({ code: 204 });
    } catch (error) {
      reject({ code: 500, payload: { message: error.message } });
    }
  });
}

/**
 * Get all products
 **/
exports.getAllProducts = function() {
  return new Promise(async function(resolve, reject) {
    try {
      const products = await Product.find({});
      resolve({ code: 200, payload: products });
    } catch (error) {
      reject({ code: 500, payload: { message: error.message } });
    }
  });
}

/**
 * Get a product by ID
 **/
exports.getProductById = function(productId) {
  return new Promise(async function(resolve, reject) {
    try {
      const product = await Product.findById(productId);
      if (!product) {
        return reject({ code: 404, payload: { message: 'Product not found' } });
      }
      resolve({ code: 200, payload: product });
    } catch (error) {
      reject({ code: 500, payload: { message: error.message } });
    }
  });
}

/**
 * Update a product
 **/
exports.updateProduct = function(body, productId) {
  return new Promise(async function(resolve, reject) {
    try {
      // { new: true } để kết quả trả về là document đã được cập nhật
      const updatedProduct = await Product.findByIdAndUpdate(productId, body, { new: true, runValidators: true });
      if (!updatedProduct) {
        return reject({ code: 404, payload: { message: 'Product not found' } });
      }
      resolve({ code: 200, payload: updatedProduct });
    } catch (error) {
      reject({ code: 400, payload: { message: error.message } });
    }
  });
}