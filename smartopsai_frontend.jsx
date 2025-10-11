import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, Cpu, Activity, CheckCircle2, MessageSquare } from "lucide-react";
import { motion } from "framer-motion";

export default function SmartOpsAIDashboard() {
  const [alerts, setAlerts] = useState([
    { id: 1, type: "Critical", message: "CPU usage at 95% on Server-03", status: "Active" },
    { id: 2, type: "Warning", message: "Disk nearing capacity on Node-07", status: "Filtered" },
    { id: 3, type: "Info", message: "Routine patch applied successfully", status: "Resolved" },
  ]);

  const [healthScore, setHealthScore] = useState(87);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([
    { sender: "AI", text: "Hi! I'm your SmartOps assistant. How can I help today?" },
  ]);

  const handleFilterAlerts = () => {
    const filtered = alerts.filter(a => a.type === "Critical");
    setAlerts(filtered);
  };

  const handleSend = () => {
    if (chatInput.trim() === "") return;
    const newMessages = [...messages, { sender: "User", text: chatInput }];
    setMessages(newMessages);
    setChatInput("");
    setTimeout(() => {
      setMessages(prev => [...prev, { sender: "AI", text: "Based on SmartOps analysis, check memory usage and restart the affected service." }]);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-200 p-6 relative">
      <header className="mb-8 text-center">
        <motion.h1 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-4xl font-bold text-gray-800">
          SmartOpsAI Dashboard
        </motion.h1>
        <p className="text-gray-500 text-lg">AI-Driven IT Operations Efficiency</p>
      </header>

      <div className="grid md:grid-cols-3 gap-6">
        {/* System Health Card */}
        <Card className="shadow-lg">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-xl font-semibold text-gray-800">
              <Activity className="text-blue-600" /> System Health
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="text-5xl font-bold text-green-600">
              {healthScore}%
            </motion.div>
            <p className="text-gray-500 mt-2">Predictive status based on real-time metrics</p>
            <Button className="mt-4" onClick={() => setHealthScore(Math.min(100, healthScore + 2))}>
              Recalculate Health
            </Button>
          </CardContent>
        </Card>

        {/* Active Alerts */}
        <Card className="shadow-lg">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-xl font-semibold text-gray-800">
              <AlertCircle className="text-red-500" /> Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {alerts.map((alert) => (
                <motion.li
                  key={alert.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-3 rounded-lg border ${
                    alert.type === "Critical"
                      ? "border-red-300 bg-red-50"
                      : alert.type === "Warning"
                      ? "border-yellow-300 bg-yellow-50"
                      : "border-green-300 bg-green-50"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-800">{alert.message}</span>
                    {alert.status === "Resolved" ? (
                      <CheckCircle2 className="text-green-500" />
                    ) : (
                      <AlertCircle className="text-red-400" />
                    )}
                  </div>
                </motion.li>
              ))}
            </ul>
            <Button className="mt-4" onClick={handleFilterAlerts}>Filter Critical Alerts</Button>
          </CardContent>
        </Card>

        {/* Patch Automation */}
        <Card className="shadow-lg">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-xl font-semibold text-gray-800">
              <Cpu className="text-purple-600" /> Patch Automation
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-600 mb-4">AI-assisted patching progress</p>
            <motion.div initial={{ width: 0 }} animate={{ width: "80%" }} className="bg-purple-500 h-4 rounded-full mx-auto"></motion.div>
            <p className="mt-2 text-gray-700">80% Complete</p>
            <Button className="mt-4">View Patch Logs</Button>
          </CardContent>
        </Card>
      </div>

      {/* Floating AI Assistant Button */}
      <Button onClick={() => setChatOpen(!chatOpen)} className="fixed bottom-6 right-6 rounded-full p-4 shadow-lg bg-blue-600 hover:bg-blue-700">
        <MessageSquare className="text-white w-6 h-6" />
      </Button>

      {/* Chat Panel */}
      {chatOpen && (
        <motion.div
          initial={{ x: 300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 300, opacity: 0 }}
          className="fixed bottom-20 right-6 bg-white shadow-2xl w-80 h-96 rounded-2xl border border-gray-300 flex flex-col"
        >
          <div className="p-4 border-b bg-blue-600 text-white font-semibold rounded-t-2xl">SmartOps Assistant</div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {messages.map((msg, i) => (
              <div key={i} className={`p-2 rounded-lg text-sm ${msg.sender === "AI" ? "bg-blue-50 text-gray-800 self-start" : "bg-gray-200 text-gray-800 self-end"}`}>
                <b>{msg.sender}:</b> {msg.text}
              </div>
            ))}
          </div>
          <div className="flex border-t p-2">
            <input
              type="text"
              className="flex-1 border rounded-l-lg p-2 text-sm focus:outline-none"
              placeholder="Ask SmartOps..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <Button className="rounded-r-lg" onClick={handleSend}>Send</Button>
          </div>
        </motion.div>
      )}

      <footer className="mt-10 text-center text-gray-500 text-sm">
        © 2025 SmartOpsAI | Team Aditya Sinha & Raisibe Sebetha
      </footer>
    </div>
  );
}
