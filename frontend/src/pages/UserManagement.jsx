import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiV2 } from '../api';
import { 
  Users, 
  Plus, 
  Mail, 
  User, 
  Shield, 
  ShieldCheck, 
  UserX, 
  UserCheck,
  Send,
  X,
  Trash2
} from 'lucide-react';

const UserManagement = () => {
  const { user, isAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteData, setInviteData] = useState({
    email: '',
    full_name: '',
    role: 'user',
    permissions: []
  });
  const [inviteLoading, setInviteLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Available permissions
  const availablePermissions = [
    { id: 'read', label: 'Read Access', description: 'View data and reports' },
    { id: 'write', label: 'Write Access', description: 'Create and edit content' },
    { id: 'generate_words', label: 'Generate Words', description: 'Generate trending words' },
    { id: 'manage_users', label: 'Manage Users', description: 'Invite and manage users' },
    { id: 'admin', label: 'Admin Access', description: 'Full administrative access' }
  ];

  useEffect(() => {
    if (isAdmin) {
      loadUsers();
    }
  }, [isAdmin]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getUsers();
      setUsers(response.data.users);
    } catch (error) {
      console.error('Failed to load users:', error);
      setError('Failed to load user list');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiV2.inviteUser({
        ...inviteData,
        permissions: inviteData.permissions.length > 0 ? inviteData.permissions : 
          (inviteData.role === 'admin' ? ['admin', 'read', 'write', 'generate_words', 'manage_users'] : ['read'])
      });

      setSuccess(`Invitation sent successfully! Temporary password: ${response.data.one_time_password}`);
      setShowInviteModal(false);
      setInviteData({ email: '', full_name: '', role: 'user', permissions: [] });
      loadUsers();
    } catch (error) {
      console.error('Failed to invite user:', error);
      setError(error.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleUserToggle = async (userId, action) => {
    try {
      if (action === 'deactivate') {
        await apiV2.deactivateUser(userId);
        setSuccess('User deactivated successfully');
      } else {
        await apiV2.activateUser(userId);
        setSuccess('User activated successfully');
      }
      loadUsers();
    } catch (error) {
      console.error('Failed to toggle user:', error);
      setError('Failed to change user status');
    }
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    
    setDeleteLoading(true);
    setError('');
    setSuccess('');

    try {
      await apiV2.deleteUser(userToDelete.id);
      setSuccess('User deleted successfully');
      setShowDeleteModal(false);
      setUserToDelete(null);
      loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      setError(error.response?.data?.detail || 'Failed to delete user');
    } finally {
      setDeleteLoading(false);
    }
  };

  const openDeleteModal = (user) => {
    setUserToDelete(user);
    setShowDeleteModal(true);
  };

  const getInitials = (name) => {
    return name.split(' ').map(word => word[0]).join('').toUpperCase();
  };

  const handlePermissionToggle = (permissionId) => {
    const currentPermissions = [...inviteData.permissions];
    const index = currentPermissions.indexOf(permissionId);
    
    if (index > -1) {
      currentPermissions.splice(index, 1);
    } else {
      currentPermissions.push(permissionId);
    }
    
    setInviteData({...inviteData, permissions: currentPermissions});
  };

  const handleRoleChange = (role) => {
    // Reset permissions when role changes
    const defaultPermissions = role === 'admin' 
      ? ['admin', 'read', 'write', 'generate_words', 'manage_users']
      : ['read'];
    
    setInviteData({
      ...inviteData, 
      role, 
      permissions: defaultPermissions
    });
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Shield className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">This page is for administrators only.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Users className="h-6 w-6 text-gray-400 mr-3" />
                <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
              </div>
              <button
                onClick={() => setShowInviteModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center transition-colors duration-200"
              >
                <Plus className="h-4 w-4 mr-2" />
                Invite New User
              </button>
            </div>
          </div>

          {error && (
            <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {success && (
            <div className="mx-6 mt-4 bg-green-50 border border-green-200 rounded-md p-4">
              <div className="text-sm text-green-700">{success}</div>
            </div>
          )}

          <div className="px-6 py-4">
            {loading ? (
              <div className="flex justify-center items-center h-32">
                <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                </svg>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {users.map((userItem) => (
                  <div key={userItem.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                          {getInitials(userItem.full_name)}
                        </div>
                        <div className="ml-3">
                          <h3 className="text-lg font-medium text-gray-900">{userItem.full_name}</h3>
                          <p className="text-sm text-gray-600">{userItem.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        {userItem.role === 'admin' ? (
                          <ShieldCheck className="h-5 w-5 text-red-500" />
                        ) : (
                          <User className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                    </div>

                    <div className="mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Role:</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          userItem.role === 'admin' 
                            ? 'bg-red-100 text-red-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {userItem.role === 'admin' ? 'Admin' : 'User'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm mt-2">
                        <span className="text-gray-600">Status:</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          userItem.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {userItem.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>

                    {userItem.id !== user.id && (
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => handleUserToggle(userItem.id, userItem.is_active ? 'deactivate' : 'activate')}
                          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors duration-200 ${
                            userItem.is_active
                              ? 'bg-red-100 text-red-700 hover:bg-red-200'
                              : 'bg-green-100 text-green-700 hover:bg-green-200'
                          }`}
                        >
                          {userItem.is_active ? (
                            <>
                              <UserX className="h-4 w-4 mr-1 inline" />
                              Deactivate
                            </>
                          ) : (
                            <>
                              <UserCheck className="h-4 w-4 mr-1 inline" />
                              Activate
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => openDeleteModal(userItem)}
                          className="px-3 py-1 rounded-md text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors duration-200"
                        >
                          <X className="h-4 w-4 mr-1 inline" />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Invite New User</h3>
              <button
                onClick={() => setShowInviteModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={inviteData.email}
                  onChange={(e) => setInviteData({...inviteData, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="user@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name (Optional)
                </label>
                <input
                  type="text"
                  value={inviteData.full_name}
                  onChange={(e) => setInviteData({...inviteData, full_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="User's full name (optional)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <select
                  value={inviteData.role}
                  onChange={(e) => handleRoleChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors duration-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 flex items-center"
                >
                  {inviteLoading ? (
                    <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                    </svg>
                  ) : (
                    <Send className="h-4 w-4 mr-2" />
                  )}
                  {inviteLoading ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && userToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="mb-4">
              <h3 className="text-lg font-medium text-gray-900">Confirm Deletion</h3>
              <p className="text-sm text-gray-600 mt-1">
                Are you sure you want to delete the user <span className="font-semibold">{userToDelete.full_name}</span>? This action cannot be undone.
              </p>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteUser}
                disabled={deleteLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors duration-200 flex items-center"
              >
                {deleteLoading ? (
                  <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                  </svg>
                ) : (
                  <X className="h-4 w-4 mr-2" />
                )}
                {deleteLoading ? 'Deleting...' : 'Delete User'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
