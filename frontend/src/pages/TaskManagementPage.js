import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { CheckCircle2, XCircle, Clock, AlertCircle, MessageSquare } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const TaskManagementPage = () => {
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [agentCommunication, setAgentCommunication] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState(null);

  // Fetch pending approvals
  const fetchPendingApprovals = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/approvals/pending`);
      const data = await response.json();

      if (data.status === 'success') {
        setPendingApprovals(data.approvals || []);
      }
    } catch (error) {
      console.error('Error fetching approvals:', error);
      toast.error('Failed to load pending approvals');
    } finally {
      setLoading(false);
    }
  };

  // Fetch agent communication
  const fetchAgentCommunication = async () => {
    try {
      const response = await fetch(`${API_URL}/agent-communication`);
      const data = await response.json();

      if (data.status === 'success') {
        setAgentCommunication(data.communication || []);
      }
    } catch (error) {
      console.error('Error fetching communication:', error);
    }
  };

  useEffect(() => {
    fetchPendingApprovals();
    fetchAgentCommunication();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchPendingApprovals();
      fetchAgentCommunication();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Approve request
  const handleApprove = async (requestId) => {
    try {
      const response = await fetch(`${API_URL}/approvals/${requestId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: 'Approved from Task Management' })
      });

      const result = await response.json();

      if (result.status === 'approved') {
        toast.success(result.message || 'Request approved successfully');
        fetchPendingApprovals(); // Refresh list
      } else {
        toast.error(result.message || 'Failed to approve request');
      }
    } catch (error) {
      console.error('Error approving:', error);
      toast.error('Error approving request');
    }
  };

  // Reject request
  const handleReject = async (requestId) => {
    try {
      const response = await fetch(`${API_URL}/approvals/${requestId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: 'Rejected from Task Management' })
      });

      const result = await response.json();

      if (result.status === 'rejected') {
        toast.success('Request rejected');
        fetchPendingApprovals();
      } else {
        toast.error(result.message || 'Failed to reject request');
      }
    } catch (error) {
      console.error('Error rejecting:', error);
      toast.error('Error rejecting request');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'approved': return <CheckCircle2 className="h-4 w-4" />;
      case 'rejected': return <XCircle className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Task Management</h1>
          <p className="text-gray-600 mt-2">
            Monitor pending approvals and agent activity
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pending Approvals Section */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Pending Approvals</CardTitle>
                <CardDescription>
                  Review and approve tasks before execution
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8 text-gray-500">
                    Loading approvals...
                  </div>
                ) : pendingApprovals.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-green-500" />
                    <p>No pending approvals</p>
                    <p className="text-sm mt-1">All tasks are approved or completed</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {pendingApprovals.map((approval) => (
                      <Card
                        key={approval.request_id}
                        className={`border-2 ${selectedApproval === approval.request_id ? 'border-blue-500' : ''}`}
                        onClick={() => setSelectedApproval(approval.request_id)}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getStatusIcon(approval.status)}
                              <CardTitle className="text-base">
                                {approval.approval_type.replace(/_/g, ' ').toUpperCase()}
                              </CardTitle>
                            </div>
                            <Badge variant={getPriorityColor(approval.priority)}>
                              {approval.priority}
                            </Badge>
                          </div>
                          <CardDescription className="text-sm">
                            Requested by {approval.requester_agent}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div>
                              <p className="font-medium text-sm mb-1">Task Description:</p>
                              <p className="text-sm text-gray-700">
                                {approval.task_description}
                              </p>
                            </div>

                            {approval.details && Object.keys(approval.details).length > 0 && (
                              <div>
                                <p className="font-medium text-sm mb-1">Details:</p>
                                <div className="bg-gray-50 p-3 rounded-md space-y-1">
                                  {Object.entries(approval.details).map(([key, value]) => (
                                    <div key={key} className="text-sm">
                                      <span className="font-medium text-gray-600">
                                        {key.replace(/_/g, ' ')}:
                                      </span>{' '}
                                      <span className="text-gray-800">{String(value)}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            <div className="flex gap-2 pt-2">
                              <Button
                                size="sm"
                                onClick={() => handleApprove(approval.request_id)}
                                className="flex-1"
                              >
                                <CheckCircle2 className="h-4 w-4 mr-1" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReject(approval.request_id)}
                                className="flex-1"
                              >
                                <XCircle className="h-4 w-4 mr-1" />
                                Reject
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Agent Communication Section */}
          <div>
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Agent Communication
                </CardTitle>
                <CardDescription>
                  Real-time agent collaboration logs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                  {agentCommunication.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 text-sm">
                      No agent communication yet
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {agentCommunication.map((comm, index) => (
                        <div key={index} className="border-l-2 border-blue-500 pl-3 py-2">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-semibold text-gray-700">
                              {comm.from} → {comm.to}
                            </p>
                            <Badge variant="outline" className="text-xs">
                              {comm.type}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">
                            {comm.message}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(comm.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator className="my-6" />

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>How Task Management Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-gray-700">
              <p>
                <strong>Approval Workflow:</strong> Critical tasks require your approval before execution.
                Review the task details and click Approve or Reject.
              </p>
              <p>
                <strong>Agent Communication:</strong> See how agents collaborate and share information
                in real-time. This helps you understand the decision-making process.
              </p>
              <p>
                <strong>Priority Levels:</strong> High priority tasks need immediate attention,
                while low priority tasks can be reviewed later.
              </p>
              <p>
                <strong>Voice Approval:</strong> You can also approve tasks using voice commands
                through the Voice Assistant page.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TaskManagementPage;
