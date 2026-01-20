"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { payeesAPI } from "@/lib/api";
import { PayeeWithCategory } from "@/types";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { PayeeIcon } from "@/components/payees/PayeeIcon";

export default function PayeesPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [payees, setPayees] = useState<PayeeWithCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadPayees();
    }
  }, [isAuthenticated]);

  const loadPayees = async () => {
    try {
      setLoading(true);
      const data = await payeesAPI.getAll();
      setPayees(data);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load payees");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this payee? Transactions will keep their payee data but won't be linked to this payee entity.")) {
      return;
    }

    try {
      await payeesAPI.delete(id);
      setPayees(payees.filter((p) => p.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete payee");
    }
  };

  const filteredPayees = payees.filter((payee) => {
    if (searchQuery && !payee.canonical_name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Sort by transaction count descending (most used first)
  const sortedPayees = [...filteredPayees].sort((a, b) => b.transaction_count - a.transaction_count);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Payees</h1>
          <button
            onClick={() => router.push("/dashboard/payees/new")}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            + Add Payee
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Search Bar */}
        <div className="mb-6 bg-white shadow rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Payees
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name..."
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading payees...</p>
          </div>
        ) : sortedPayees.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Payee Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Default Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transactions
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedPayees.map((payee) => (
                  <tr key={payee.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <PayeeIcon
                          logoUrl={payee.logo_url}
                          name={payee.canonical_name}
                          size={36}
                          className="mr-3"
                        />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {payee.canonical_name}
                          </div>
                          {payee.notes && (
                            <div className="text-xs text-gray-500 truncate max-w-xs">
                              {payee.notes}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {payee.payee_type ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                          {payee.payee_type}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {payee.default_category_name ? (
                        <button
                          onClick={() => router.push(`/dashboard/categories`)}
                          className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {payee.default_category_name}
                        </button>
                      ) : (
                        <span className="text-sm text-gray-400">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 font-medium">
                        {payee.transaction_count}
                      </span>
                      <span className="text-xs text-gray-500 ml-1">transactions</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/dashboard/payees/${payee.id}`)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(payee.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 mb-4">
              {payees.length === 0
                ? "No payees yet. Payees are automatically created when you add transactions."
                : "No payees match your search"}
            </p>
            {payees.length === 0 && (
              <button
                onClick={() => router.push("/dashboard/transactions")}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Go to Transactions
              </button>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
