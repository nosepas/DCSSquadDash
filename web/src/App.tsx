import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Loading } from './components/states/Loading';
import { useAuth } from './features/auth/AuthContext';
import { RequireAdmin, RequireAuth } from './features/auth/guards';

const DashboardPage = lazy(() => import('./features/dashboard/DashboardPage'));
const MapPage = lazy(() => import('./features/map/MapPage'));
const MissionsPage = lazy(() => import('./features/missions/MissionsPage'));
const ObjectivesPage = lazy(() => import('./features/objectives/ObjectivesPage'));
const RankingPage = lazy(() => import('./features/ranking/RankingPage'));
const KillsPage = lazy(() => import('./features/kills/KillsPage'));
const PlayersPage = lazy(() => import('./features/players/PlayersPage'));
const ProfilePage = lazy(() => import('./features/players/ProfilePage'));
const MyProfilePage = lazy(() => import('./features/players/MyProfilePage'));
const LoginPage = lazy(() => import('./features/auth/LoginPage'));
const AdminLayout = lazy(() => import('./features/admin/AdminLayout'));
const ServersAdmin = lazy(() => import('./features/admin/ServersAdmin'));
const ServerDetailPage = lazy(() => import('./features/admin/server/ServerDetailPage'));
const TacviewPage = lazy(() => import('./features/tacview/TacviewPage'));
const DtcPage = lazy(() => import('./features/dtc/DtcPage'));
const AgentsAdmin = lazy(() => import('./features/admin/AgentsAdmin'));
const UsersAdmin = lazy(() => import('./features/admin/UsersAdmin'));
const NotFoundPage = lazy(() => import('./features/misc/NotFoundPage'));

/** "/" is the private dashboard; visitors who are not signed in land on the public map instead. */
function Home() {
  const { status } = useAuth();
  if (status === 'loading') return <Loading />;
  if (status === 'anon') return <Navigate to="/map" replace />;
  return <DashboardPage />;
}

export function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Home />} />
          <Route path="map" element={<MapPage />} />
          <Route path="missions" element={<MissionsPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route path="objectives" element={<ObjectivesPage />} />
            <Route path="ranking" element={<RankingPage />} />
            <Route path="kills" element={<KillsPage />} />
            <Route path="tacview" element={<TacviewPage />} />
            <Route path="dtc" element={<DtcPage />} />
            <Route path="players" element={<PlayersPage />} />
            <Route path="players/:ucid" element={<ProfilePage />} />
            <Route path="profile" element={<MyProfilePage />} />
            <Route element={<RequireAdmin />}>
              <Route path="admin" element={<AdminLayout />}>
                <Route index element={<ServersAdmin />} />
                <Route path="servers/:id" element={<ServerDetailPage />} />
                <Route path="agents" element={<AgentsAdmin />} />
                <Route path="users" element={<UsersAdmin />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
