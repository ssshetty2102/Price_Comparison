import React, { useState } from 'react';

function App() {
    const [productName, setProductName] = useState('');
    const [comparisonData, setComparisonData] = useState(null);
    const [error, setError] = useState('');
    const backendUrl = 'http://localhost:8002/compare-prices/'; 

    const handleInputChange = (event) => {
        setProductName(event.target.value);
    };

    const handleCompareClick = async () => {
        setError('');
        setComparisonData(null);

        if (!productName.trim()) {
            setError('Please enter a product name.');
            return;
        }

        try {
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ product_name: productName }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setComparisonData(data);
        } catch (e) {
            setError(`Failed to fetch data: ${e.message}`);
        }
    };

    return (
        <div className="container mx-auto p-8">
            <h1 className="text-3xl font-bold mb-6 text-center text-indigo-700">Price Comparison</h1>
            <div className="input-group flex mb-4">
                <input
                    type="text"
                    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                    placeholder="Enter product name (e.g., laptop)"
                    value={productName}
                    onChange={handleInputChange}
                />
                <button
                    className="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ml-2"
                    onClick={handleCompareClick}
                >
                    Compare Prices
                </button>
            </div>

            {error && <p className="text-red-500 italic">{error}</p>}

            {comparisonData && (
                <div className="mt-8">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">Comparison Results:</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="result-card border rounded p-4">
                            <h3 className="font-semibold text-lg text-blue-600 mb-2">Snapdeal</h3>
                            {comparisonData.Snapdeal && comparisonData.Snapdeal.error ? (
                                <p className="text-red-500">{comparisonData.Snapdeal.error}</p>
                            ) : comparisonData.Snapdeal && comparisonData.Snapdeal.message ? (
                                <p className="text-gray-600">{comparisonData.Snapdeal.message}</p>
                            ) : (
                                comparisonData.Snapdeal && (
                                    <div>
                                        <p><span className="font-semibold">Price:</span> {comparisonData.Snapdeal.price}</p>
                                        <a href={comparisonData.Snapdeal.link} target="_blank" rel="noopener noreferrer" className="link-button mt-2">View on Snapdeal</a>
                                    </div>
                                )
                            )}
                        </div>

                        <div className="result-card border rounded p-4">
                            <h3 className="font-semibold text-lg text-green-600 mb-2">Shopclues</h3>
                            {comparisonData.Shopclues && comparisonData.Shopclues.error ? (
                                <p className="text-red-500">{comparisonData.Shopclues.error}</p>
                            ) : comparisonData.Shopclues && comparisonData.Shopclues.message ? (
                                <p className="text-gray-600">{comparisonData.Shopclues.message}</p>
                            ) : (
                                comparisonData.Shopclues && (
                                    <div>
                                        <p><span className="font-semibold">Price:</span> {comparisonData.Shopclues.price}</p>
                                        <a href={comparisonData.Shopclues.link} target="_blank" rel="noopener noreferrer" className="link-button mt-2">View on Shopclues</a>
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;