import React, { useState } from 'react';
import { Send } from 'lucide-react';

// Define props interface to fix TypeScript error
interface SurveyFormProps {
  onSubmitSuccess?: () => void;
}

const SurveyForm: React.FC<SurveyFormProps> = ({ onSubmitSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    "Name of Child ": "",
    "Age": "",
    "Class (बच्चे की कक्षा)": "",
    "Background of the Child ": "",
    "Problems in Home ": "",
    "Behavioral Impact": "",
    "Academic Performance ": "",
    "Family Income ": "",
    "Role models": "",
    "Reason for such role model ": ""
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Format data for backend
      const submissionData = {
        ...formData,
        "Age": parseFloat(formData["Age"]),
        "Class (बच्चे की कक्षा)": parseFloat(formData["Class (बच्चे की कक्षा)"]),
        "Academic Performance ": parseFloat(formData["Academic Performance "]),
        "Family Income ": parseFloat(formData["Family Income "])
      };

      // Submit to backend
      const response = await fetch('http://localhost:5000/api/submit-survey', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });

      if (response.ok) {
        alert('Survey submitted successfully!');
        
        // Clear form
        setFormData({
          "Name of Child ": "",
          "Age": "",
          "Class (बच्चे की कक्षा)": "",
          "Background of the Child ": "",
          "Problems in Home ": "",
          "Behavioral Impact": "",
          "Academic Performance ": "",
          "Family Income ": "",
          "Role models": "",
          "Reason for such role model ": ""
        });
        
        // Call the callback if it exists
        if (onSubmitSuccess) {
          onSubmitSuccess();
        }
      } else {
        throw new Error('Failed to submit survey');
      }
    } catch (error) {
      console.error('Error submitting survey:', error);
      alert('Failed to submit survey. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-md p-8 mt-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Career Guidance Survey</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Child Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name of Child
            </label>
            <input
              type="text"
              name="Name of Child "
              value={formData["Name of Child "]}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Age
            </label>
            <input
              type="number"
              name="Age"
              value={formData["Age"]}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Class (बच्चे की कक्षा)
          </label>
          <input
            type="number"
            name="Class (बच्चे की कक्षा)"
            value={formData["Class (बच्चे की कक्षा)"]}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Background and Environment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Background of the Child (e.g., Middle Class, Labour, Private Job)
          </label>
          <input
            type="text"
            name="Background of the Child "
            value={formData["Background of the Child "]}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Problems in Home (e.g., Financial, Family, Health)
          </label>
          <input
            type="text"
            name="Problems in Home "
            value={formData["Problems in Home "]}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Behavioral Impact
          </label>
          <textarea
            name="Behavioral Impact"
            value={formData["Behavioral Impact"]}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            rows={3}
            placeholder="Describe the child's behavior (e.g., Lack of Confidence, No effect, Aggressive)"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Academic Performance (Scale 1-10)
            </label>
            <input
              type="number"
              name="Academic Performance "
              value={formData["Academic Performance "]}
              onChange={handleChange}
              min="1"
              max="10"
              required
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Family Income (Monthly in Rupees)
            </label>
            <input
              type="number"
              name="Family Income "
              value={formData["Family Income "]}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        {/* Role Models */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Role Models (e.g., Teacher, Doctor, Army, Guardian)
          </label>
          <input
            type="text"
            name="Role models"
            value={formData["Role models"]}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason for such role model
          </label>
          <textarea
            name="Reason for such role model "
            value={formData["Reason for such role model "]}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            rows={3}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2"
        >
          {loading ? (
            <span>Processing...</span>
          ) : (
            <>
              <Send className="h-5 w-5" />
              <span>Submit Survey</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default SurveyForm;
