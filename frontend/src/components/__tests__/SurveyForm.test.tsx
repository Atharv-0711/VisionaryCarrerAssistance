import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SurveyForm from '../SurveyForm';
import userEvent from '@testing-library/user-event';

describe('SurveyForm Component', () => {
  const mockSubmitSuccess = jest.fn();

  beforeEach(() => {
    mockSubmitSuccess.mockClear();
  });

  it('renders all form fields', () => {
    render(<SurveyForm onSubmitSuccess={mockSubmitSuccess} />);
    
    // Check for form fields using htmlFor/id associations
    expect(screen.getByLabelText('Name of Child')).toBeInTheDocument();
    expect(screen.getByLabelText('Age')).toBeInTheDocument();
    expect(screen.getByLabelText('Class (बच्चे की कक्षा)')).toBeInTheDocument();
    expect(screen.getByLabelText('Background of the Child (e.g., Middle Class, Labour, Private Job)')).toBeInTheDocument();
    expect(screen.getByLabelText('Problems in Home (e.g., Financial, Family, Health)')).toBeInTheDocument();
    expect(screen.getByLabelText('Behavioral Impact')).toBeInTheDocument();
    expect(screen.getByLabelText('Academic Performance (Scale 1-10)')).toBeInTheDocument();
    expect(screen.getByLabelText('Family Income (Monthly in Rupees)')).toBeInTheDocument();
    expect(screen.getByLabelText('Role Models (e.g., Teacher, Doctor, Army, Guardian)')).toBeInTheDocument();
    expect(screen.getByLabelText('Reason for such role model')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<SurveyForm onSubmitSuccess={mockSubmitSuccess} />);
    
    // Try to submit without filling required fields
    fireEvent.click(screen.getByRole('button', { name: /submit survey/i }));
    
    // Check for HTML5 validation
    const nameInput = screen.getByLabelText('Name of Child');
    expect(nameInput).toBeRequired();
    
    const ageInput = screen.getByLabelText('Age');
    expect(ageInput).toBeRequired();
    
    const classInput = screen.getByLabelText('Class (बच्चे की कक्षा)');
    expect(classInput).toBeRequired();
  });

  it('submits form with valid data', async () => {
    render(<SurveyForm onSubmitSuccess={mockSubmitSuccess} />);
    
    // Fill in form with valid data
    fireEvent.change(screen.getByLabelText('Name of Child'), { target: { value: 'John Doe' } });
    fireEvent.change(screen.getByLabelText('Age'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Class (बच्चे की कक्षा)'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Background of the Child (e.g., Middle Class, Labour, Private Job)'), { target: { value: 'Middle class' } });
    fireEvent.change(screen.getByLabelText('Problems in Home (e.g., Financial, Family, Health)'), { target: { value: 'None' } });
    fireEvent.change(screen.getByLabelText('Behavioral Impact'), { target: { value: 'Positive' } });
    fireEvent.change(screen.getByLabelText('Academic Performance (Scale 1-10)'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Family Income (Monthly in Rupees)'), { target: { value: '50000' } });
    fireEvent.change(screen.getByLabelText('Role Models (e.g., Teacher, Doctor, Army, Guardian)'), { target: { value: 'Parents' } });
    fireEvent.change(screen.getByLabelText('Reason for such role model'), { target: { value: 'Inspiration' } });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit survey/i }));

    // Check if onSubmitSuccess was called
    await waitFor(() => {
      expect(mockSubmitSuccess).toHaveBeenCalled();
    });
  });

  it('handles form reset', async () => {
    render(<SurveyForm onSubmitSuccess={mockSubmitSuccess} />);
    
    // Fill in some data
    const nameInput = screen.getByLabelText('Name of Child');
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    // Reset form
    fireEvent.click(screen.getByRole('button', { name: /reset/i }));
    
    // Check if fields are cleared
    expect(nameInput).toHaveValue('');
  });
}); 