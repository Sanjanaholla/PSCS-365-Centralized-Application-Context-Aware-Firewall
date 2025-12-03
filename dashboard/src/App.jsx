import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw, Zap, AlertTriangle, CheckCircle } from 'lucide-react'; // Example icons

// Base URL for the FastAPI backend. Use 127.0.0.1 to avoid potential CORS issues with localhost
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1/policies/'; 


/**
 * Helper component to render the status with distinct colors and shapes.
 * This simulates a status based on a simple calculation for display purposes.
 */
const StatusBadge = ({ policy }) => {
  let status, colorClasses, Icon;
  
  // Example logic to determine status for display:
  if (policy.action === 'DENY' && policy.port > 10000) {
    status = "High Risk Policy";
    colorClasses = 'bg-red-100 text-red-800 border-red-300';
    Icon = AlertTriangle;
  } else if (policy.app_name.includes("Unknown")) {
    status = "Unidentified App";
    colorClasses = 'bg-yellow-100 text-yellow-800 border-yellow-300';
    Icon = Zap;
  } else {
    status = "Active & Enforced";
    colorClasses = 'bg-green-100 text-green-800 border-green-300';
    Icon = CheckCircle;
  }

  return (
    <span 
      className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full border ${colorClasses} transition duration-150 ease-in-out`}
    >
      <Icon size={12} />
      {status}
    </span>
  );
};

/**
 * Component to display the list of policies fetched from the backend.
 */
const PolicyAssignmentTable = ({ policies, isLoading, fetchError, refreshPolicies }) => {
  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading policies...</div>;
  }

  if (fetchError) {
    return (
      <div className="text-center py-12 bg-red-50 border-l-4 border-red-400 p-4 rounded-lg shadow-sm">
        <p className="text-red-700 font-semibold">Error fetching data: {fetchError}</p>
        <p className="text-sm text-red-600">
          Make sure the FastAPI backend is running at <code className="font-mono">{API_BASE_URL}</code>.
        </p>
      </div>
    );
  }

  if (policies.length === 0) {
    return <div className="text-center py-12 text-gray-500">No policies found. Add a new policy via the API.</div>;
  }

  return (
    <div className="overflow-x-auto shadow-xl rounded-lg border border-gray-100">
      <table className="min-w-full divide-y divide-gray-200">
        {/* Table Header */}
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Policy ID
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Application Name
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Rule (Protocol:Port)
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Status/Action
            </th>
            <th scope="col" className="relative px-6 py-3">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        
        {/* Table Body */}
        <tbody className="bg-white divide-y divide-gray-200">
          {policies.map((policy) => (
            <tr key={policy.id} className="hover:bg-indigo-50/50 transition duration-100 ease-in-out">
              
              {/* Policy ID */}
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-500">
                {policy.id}
              </td>
              
              {/* Application Name */}
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">{policy.app_name}</div>
              </td>
              
              {/* Rule */}
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                <span className="font-semibold text-indigo-600">{policy.protocol}</span>
                <span className="text-gray-400">/</span>
                <span className="font-semibold text-indigo-600">{policy.port}</span>
                <span className="ml-3 px-2 py-0.5 text-xs rounded-full bg-gray-200 text-gray-800">
                  {policy.action}
                </span>
              </td>
              
              {/* Status Indicator */}
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusBadge policy={policy} />
              </td>
              
              {/* Action Button */}
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <a href="#" className="text-indigo-600 hover:text-indigo-900 font-semibold transition duration-150">
                  Edit
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};


// Main App component to host the table and set the overall layout
const App = () => {
  const [policies, setPolicies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Function to fetch data from the FastAPI backend
  const fetchPolicies = async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const response = await axios.get(API_BASE_URL);
      setPolicies(response.data);
    } catch (error) {
      console.error("Fetch error:", error);
      setFetchError(error.message);
      setPolicies([]); // Clear policies on error
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch policies when the component mounts
  useEffect(() => {
    fetchPolicies();
  }, []);

  return (
    <div className="p-4 sm:p-8 md:p-10 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-6xl mx-auto">
        
        {/* Title Card and Refresh Button */}
        <header className="mb-8 p-6 bg-white shadow-lg rounded-xl border-l-4 border-indigo-600 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Centralized Policy Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">
              Policies defined in the FastAPI backend and their simulated enforcement status.
            </p>
          </div>
          <button
            onClick={fetchPolicies}
            disabled={isLoading}
            className={`flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 transition duration-150 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
            {isLoading ? 'Refreshing...' : 'Refresh Policies'}
          </button>
        </header>

        {/* The Table Component */}
        <PolicyAssignmentTable 
          policies={policies} 
          isLoading={isLoading} 
          fetchError={fetchError}
          refreshPolicies={fetchPolicies}
        />
        
        {/* Footer/Summary */}
        <div className="mt-6 text-sm text-gray-600 text-center">
          Showing {policies.length} deployed policies.
        </div>

      </div>
    </div>
  );
};

export default App;