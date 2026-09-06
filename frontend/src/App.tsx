import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import InboxPage from './pages/InboxPage';
import BacklogPage from './pages/BacklogPage';
import BoardPage from './pages/BoardPage';
import ArchivePage from './pages/ArchivePage';
import TaskFormPage from './pages/TaskFormPage';
import TaskDetailPage from './pages/TaskDetailPage';
import AssigneesPage from './pages/AssigneesPage';
import SprintsPage from './pages/SprintsPage';
import ReportsPage from './pages/ReportsPage';
import PromptBuilderPage from './pages/PromptBuilderPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/board" replace />} />
        <Route path="/inbox" element={<InboxPage />} />
        <Route path="/board" element={<BoardPage />} />
        <Route path="/backlog" element={<BacklogPage />} />
        <Route path="/archive" element={<ArchivePage />} />
        <Route path="/tasks/new" element={<TaskFormPage />} />
        <Route path="/tasks/:id" element={<TaskDetailPage />} />
        <Route path="/tasks/:id/edit" element={<TaskFormPage />} />
        <Route path="/assignees" element={<AssigneesPage />} />
        <Route path="/sprints" element={<SprintsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/prompts" element={<PromptBuilderPage />} />
      </Route>
    </Routes>
  );
}
