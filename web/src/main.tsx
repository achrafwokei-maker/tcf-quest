import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import "@fontsource/anton";
import "@fontsource-variable/nunito";
import "./styles/index.css";
import { api } from "./lib/api";
import { useAsync } from "./lib/useAsync";
import { AppShell } from "./components/AppShell";
import { ErrorNote, Loading } from "./components/ui";
import { Onboarding } from "./pages/Onboarding";
import { Today } from "./pages/Today";
import { Journey } from "./pages/Journey";
import { Practice } from "./pages/Practice";
import { Progress } from "./pages/Progress";
import { Tutor } from "./pages/Tutor";
import { AvatarPage } from "./pages/AvatarPage";
import { ExercisePlayer } from "./pages/ExercisePlayer";
import { ReviewPage } from "./pages/ReviewPage";
import { NotebookPage } from "./pages/NotebookPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WritingList, WritingStudio } from "./pages/WritingPage";
import { SpeakingPage } from "./pages/SpeakingPage";
import { EOSessionPage } from "./pages/EOPage";
import { ExamList, ExamRunner } from "./pages/ExamPage";
import { LibraryPage } from "./pages/LibraryPage";

function App() {
  const [state, reload] = useAsync(api.profile);
  const navigate = useNavigate();
  const afterOnboarding = (avatarNow: boolean) => {
    reload();
    navigate(avatarNow ? "/avatar" : "/aventure");
  };

  if (state.status === "loading") return <div className="mx-auto max-w-xl px-6"><Loading /></div>;
  if (state.status === "error")
    return <div className="mx-auto max-w-xl px-6 py-16"><ErrorNote error={state.error} onRetry={reload} /></div>;
  if (!state.data.profile?.onboarded_at) return <Onboarding onDone={afterOnboarding} />;

  return (
    <Routes>
      <Route path="set/:setId" element={<ExercisePlayer />} />
      <Route path="examen/:attemptId" element={<ExamRunner />} />
      <Route path="bienvenue" element={<Onboarding onDone={afterOnboarding} />} />
      <Route element={<AppShell />}>
        <Route index element={<Today />} />
        <Route path="aventure" element={<Journey />} />
        <Route path="entrainement" element={<Practice />} />
        <Route path="progression" element={<Progress />} />
        <Route path="professeur" element={<Tutor />} />
        <Route path="avatar" element={<AvatarPage />} />
        <Route path="review" element={<ReviewPage />} />
        <Route path="carnet" element={<NotebookPage />} />
        <Route path="reglages" element={<SettingsPage />} />
        <Route path="ecrit" element={<WritingList />} />
        <Route path="oral" element={<SpeakingPage />} />
        <Route path="oral/:taskId" element={<EOSessionPage />} />
        <Route path="examen" element={<ExamList />} />
        <Route path="academie" element={<LibraryPage context="academy" eyebrow="Académie TCF" title="Strategies for every task"
          intro="Each module: the method, an example, guided practice with hints, practice on your own, a timed question, then the real task." />} />
        <Route path="pratique/CO" element={<LibraryPage section="CO" eyebrow="Compréhension orale" title="Listening"
          intro="Everything that trains TCF listening: strategies, practice sets and story missions. Exam-style listening is in Examens." />} />
        <Route path="pratique/CE" element={<LibraryPage section="CE" eyebrow="Compréhension écrite" title="Reading"
          intro="Everything that trains TCF reading: strategies, practice sets and lessons. Exam-style reading is in Examens." />} />
        <Route path="outils" element={<LibraryPage context="toolbox" eyebrow="Boîte à outils" title="Frameworks, connectors, grammar"
          intro="Short lessons: what it is, when to use it, when not to, an example, then you adapt it and practise. Your weak points bring the right lesson to your plan." />} />
        <Route path="ecrit/:taskId" element={<WritingStudio />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
