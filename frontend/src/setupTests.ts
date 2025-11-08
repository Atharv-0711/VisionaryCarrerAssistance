import '@testing-library/jest-dom';

// Mock the fetch function globally
global.fetch = jest.fn();

// Mock the console.error to keep test output clean
console.error = jest.fn(); 